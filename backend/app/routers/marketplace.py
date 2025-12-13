"""
Маркетплейс API
- Sellers (Партнеры)
- Listings (Барахолка)
- Statistics
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from .. import models, schemas
from ..database import get_db
from ..bot import bot, ADMIN_CHAT_IDS

router = APIRouter(prefix="/marketplace", tags=["Marketplace"])


# ============ SELLERS (Партнеры) ============

@router.post("/sellers/apply", response_model=schemas.Seller)
async def apply_as_seller(
    seller_data: schemas.SellerCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Подать заявку на партнерство.
    После подачи заявка уходит на модерацию к админу.
    """
    # Проверяем, нет ли уже такого продавца
    result = await db.execute(
        select(models.Seller).where(models.Seller.telegram_id == seller_data.telegram_id)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Заявка уже существует. Статус: {existing.status}"
        )
    
    # Создаем заявку
    new_seller = models.Seller(
        name=seller_data.name,
        contact_name=seller_data.contact_name,
        phone=seller_data.phone,
        email=seller_data.email,
        telegram_id=seller_data.telegram_id,
        telegram_username=seller_data.telegram_username,
        description=seller_data.description,
        status=models.SellerStatus.PENDING.value,
        subscription_tier=models.SubscriptionTier.FREE.value,
        max_products=10,  # Бесплатный лимит
    )
    
    db.add(new_seller)
    await db.commit()
    await db.refresh(new_seller)
    
    # Уведомляем админа
    background_tasks.add_task(notify_seller_application, new_seller)
    
    return new_seller


@router.get("/sellers/me", response_model=schemas.Seller)
async def get_my_seller_profile(
    telegram_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Получить свой профиль продавца по Telegram ID"""
    result = await db.execute(
        select(models.Seller).where(models.Seller.telegram_id == telegram_id)
    )
    seller = result.scalar_one_or_none()
    
    if not seller:
        raise HTTPException(status_code=404, detail="Профиль продавца не найден")
    
    return seller


@router.get("/sellers/me/stats", response_model=schemas.SellerStats)
async def get_my_seller_stats(
    telegram_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Получить статистику для кабинета партнера"""
    result = await db.execute(
        select(models.Seller).where(models.Seller.telegram_id == telegram_id)
    )
    seller = result.scalar_one_or_none()
    
    if not seller:
        raise HTTPException(status_code=404, detail="Профиль продавца не найден")
    
    # Считаем товары
    products_result = await db.execute(
        select(func.count(models.Product.id)).where(models.Product.seller_id == seller.id)
    )
    total_products = products_result.scalar() or 0
    
    # Считаем заказы (TODO: связать с seller_id в OrderItem)
    total_orders = seller.total_sales
    
    return schemas.SellerStats(
        total_products=total_products,
        total_views=seller.total_views,
        total_orders=total_orders,
        products_limit=seller.max_products,
        subscription_tier=seller.subscription_tier,
        subscription_expires=seller.subscription_expires
    )


@router.get("/sellers/pending", response_model=List[schemas.Seller])
async def get_pending_sellers(db: AsyncSession = Depends(get_db)):
    """[Админ] Получить заявки на модерацию"""
    result = await db.execute(
        select(models.Seller)
        .where(models.Seller.status == models.SellerStatus.PENDING.value)
        .order_by(models.Seller.created_at.desc())
    )
    return result.scalars().all()


@router.get("/sellers/", response_model=List[schemas.Seller])
async def get_all_sellers(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """[Админ] Получить всех продавцов"""
    query = select(models.Seller).order_by(models.Seller.created_at.desc())
    if status:
        query = query.where(models.Seller.status == status)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.put("/sellers/{seller_id}", response_model=schemas.Seller)
async def update_seller(
    seller_id: int,
    seller_data: schemas.SellerUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """[Админ] Обновить продавца (модерация, верификация, подписка)"""
    result = await db.execute(
        select(models.Seller).where(models.Seller.id == seller_id)
    )
    seller = result.scalar_one_or_none()
    
    if not seller:
        raise HTTPException(status_code=404, detail="Продавец не найден")
    
    old_status = seller.status
    
    # Обновляем поля
    update_data = seller_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(seller, field):
            setattr(seller, field, value)
    
    # Обновляем лимит товаров по подписке
    if seller_data.subscription_tier:
        tier_limits = {
            "free": 10,
            "start": 50,
            "pro": 1000,
            "magnate": 999999,
        }
        seller.max_products = tier_limits.get(seller_data.subscription_tier, 10)
    
    await db.commit()
    await db.refresh(seller)
    
    # Уведомляем продавца, если статус изменился
    if old_status != seller.status:
        background_tasks.add_task(notify_seller_status_change, seller)
    
    return seller


# ============ LISTINGS (Барахолка) ============

@router.post("/listings/", response_model=schemas.Listing)
async def create_listing(
    listing_data: schemas.ListingCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Создать объявление в Барахолке.
    Статус: draft (нужна оплата) -> pending (на модерации) -> approved
    """
    new_listing = models.Listing(
        title=listing_data.title,
        description=listing_data.description,
        price=listing_data.price,
        city=listing_data.city,
        images=listing_data.images,
        seller_name=listing_data.seller_name,
        seller_phone=listing_data.seller_phone,
        seller_telegram_id=listing_data.seller_telegram_id,
        seller_telegram_username=listing_data.seller_telegram_username,
        status=models.ListingStatus.DRAFT.value,
        payment_amount=200.0,  # Стоимость размещения
        expires_at=datetime.utcnow() + timedelta(days=30),  # 30 дней
    )
    
    db.add(new_listing)
    await db.commit()
    await db.refresh(new_listing)
    
    return new_listing


@router.post("/listings/{listing_id}/pay")
async def mark_listing_paid(
    listing_id: int,
    payment_id: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Отметить объявление как оплаченное.
    После оплаты статус меняется на 'pending' (на модерации).
    """
    result = await db.execute(
        select(models.Listing).where(models.Listing.id == listing_id)
    )
    listing = result.scalar_one_or_none()
    
    if not listing:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    
    listing.is_paid = True
    listing.payment_id = payment_id
    listing.status = models.ListingStatus.PENDING.value
    
    await db.commit()
    
    # Уведомляем админа
    if background_tasks:
        background_tasks.add_task(notify_listing_pending, listing)
    
    return {"status": "ok", "message": "Объявление отправлено на модерацию"}


@router.get("/listings/", response_model=List[schemas.ListingPublic])
async def get_listings(
    skip: int = 0,
    limit: int = 20,
    city: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Получить одобренные объявления (для ленты)"""
    query = select(models.Listing).where(
        models.Listing.status == models.ListingStatus.APPROVED.value
    )
    
    if city:
        query = query.where(models.Listing.city.ilike(f"%{city}%"))
    
    # Сначала promoted, потом по дате
    query = query.order_by(
        models.Listing.is_promoted.desc(),
        models.Listing.created_at.desc()
    ).offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/listings/pending", response_model=List[schemas.Listing])
async def get_pending_listings(db: AsyncSession = Depends(get_db)):
    """[Админ] Получить объявления на модерацию"""
    result = await db.execute(
        select(models.Listing)
        .where(models.Listing.status == models.ListingStatus.PENDING.value)
        .order_by(models.Listing.created_at.desc())
    )
    return result.scalars().all()


@router.get("/listings/my", response_model=List[schemas.Listing])
async def get_my_listings(
    telegram_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Получить свои объявления"""
    result = await db.execute(
        select(models.Listing)
        .where(models.Listing.seller_telegram_id == telegram_id)
        .order_by(models.Listing.created_at.desc())
    )
    return result.scalars().all()


@router.get("/listings/{listing_id}", response_model=schemas.Listing)
async def get_listing(listing_id: int, db: AsyncSession = Depends(get_db)):
    """Получить объявление по ID"""
    result = await db.execute(
        select(models.Listing).where(models.Listing.id == listing_id)
    )
    listing = result.scalar_one_or_none()
    
    if not listing:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    
    # Увеличиваем счетчик просмотров
    listing.views_count += 1
    await db.commit()
    
    return listing


@router.put("/listings/{listing_id}", response_model=schemas.Listing)
async def update_listing(
    listing_id: int,
    listing_data: schemas.ListingUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """[Админ] Обновить объявление (модерация)"""
    result = await db.execute(
        select(models.Listing).where(models.Listing.id == listing_id)
    )
    listing = result.scalar_one_or_none()
    
    if not listing:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    
    old_status = listing.status
    
    update_data = listing_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(listing, field):
            setattr(listing, field, value)
    
    await db.commit()
    await db.refresh(listing)
    
    # Уведомляем продавца или админа
    if old_status != listing.status:
        if listing.status == models.ListingStatus.PENDING.value:
            background_tasks.add_task(notify_listing_pending, listing)
        else:
            background_tasks.add_task(notify_listing_status_change, listing)
    
    return listing


# ============ SELLER PRODUCTS ============

@router.get("/sellers/me/products", response_model=List[schemas.Product])
async def get_my_products(
    telegram_id: str,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Получить товары партнера"""
    # Найти продавца
    result = await db.execute(
        select(models.Seller).where(models.Seller.telegram_id == telegram_id)
    )
    seller = result.scalar_one_or_none()
    
    if not seller:
        raise HTTPException(status_code=404, detail="Продавец не найден")
    
    if seller.status != "approved":
        raise HTTPException(status_code=403, detail="Аккаунт не активен")
    
    # Получить товары
    products_result = await db.execute(
        select(models.Product)
        .where(models.Product.seller_id == seller.id)
        .order_by(models.Product.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    
    return products_result.scalars().all()


@router.post("/sellers/me/products", response_model=schemas.Product)
async def create_seller_product(
    telegram_id: str,
    product_data: schemas.ProductCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создать товар от имени партнера"""
    # Найти продавца
    result = await db.execute(
        select(models.Seller).where(models.Seller.telegram_id == telegram_id)
    )
    seller = result.scalar_one_or_none()
    
    if not seller:
        raise HTTPException(status_code=404, detail="Продавец не найден")
    
    if seller.status != "approved":
        raise HTTPException(status_code=403, detail="Аккаунт не активен")
    
    # Проверить лимит товаров
    count_result = await db.execute(
        select(func.count(models.Product.id)).where(models.Product.seller_id == seller.id)
    )
    current_count = count_result.scalar() or 0
    
    if current_count >= seller.max_products:
        raise HTTPException(
            status_code=400, 
            detail=f"Достигнут лимит товаров ({seller.max_products}). Обновите подписку."
        )
    
    # Проверить уникальность артикула
    existing = await db.execute(
        select(models.Product).where(models.Product.part_number == product_data.part_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Товар с таким артикулом уже существует")
    
    # Создать товар
    new_product = models.Product(
        name=product_data.name,
        part_number=product_data.part_number,
        description=product_data.description,
        manufacturer=product_data.manufacturer,
        price_rub=product_data.price_rub,
        stock_quantity=product_data.stock_quantity or 1,
        is_in_stock=True,
        category_id=product_data.category_id,
        image_url=product_data.image_url,
        seller_id=seller.id,  # Привязываем к продавцу
        views_count=0
    )
    
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    
    return new_product


@router.delete("/sellers/me/products/{product_id}")
async def delete_seller_product(
    product_id: int,
    telegram_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Удалить товар партнера"""
    # Найти продавца
    seller_result = await db.execute(
        select(models.Seller).where(models.Seller.telegram_id == telegram_id)
    )
    seller = seller_result.scalar_one_or_none()
    
    if not seller:
        raise HTTPException(status_code=404, detail="Продавец не найден")
    
    # Найти товар
    product_result = await db.execute(
        select(models.Product).where(
            models.Product.id == product_id,
            models.Product.seller_id == seller.id
        )
    )
    product = product_result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден или не принадлежит вам")
    
    await db.delete(product)
    await db.commit()
    
    return {"status": "ok", "message": "Товар удален"}


# ============ PRODUCT VIEWS (Статистика) ============

@router.post("/products/{product_id}/view")
async def record_product_view(
    product_id: int,
    viewer_telegram_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Записать просмотр товара"""
    # Проверяем, что товар существует
    result = await db.execute(
        select(models.Product).where(models.Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    # Увеличиваем счетчик
    product.views_count = (product.views_count or 0) + 1
    
    # Записываем в историю (для детальной статистики)
    view = models.ProductView(
        product_id=product_id,
        viewer_telegram_id=viewer_telegram_id
    )
    db.add(view)
    
    # Если товар принадлежит продавцу — обновляем его статистику
    if product.seller_id:
        seller_result = await db.execute(
            select(models.Seller).where(models.Seller.id == product.seller_id)
        )
        seller = seller_result.scalar_one_or_none()
        if seller:
            seller.total_views = (seller.total_views or 0) + 1
    
    await db.commit()
    
    return {"status": "ok"}


# ============ NOTIFICATIONS ============

async def notify_seller_application(seller: models.Seller):
    """Уведомление админу о новой заявке партнера"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
    
    if not bot or not ADMIN_CHAT_IDS:
        return
    
    text = (
        f"🆕 <b>Новая заявка на партнерство!</b>\n\n"
        f"🏪 <b>{seller.name}</b>\n"
        f"👤 Контакт: {seller.contact_name or 'Не указан'}\n"
        f"📞 Телефон: {seller.phone or 'Не указан'}\n"
        f"📧 Email: {seller.email or 'Не указан'}\n"
        f"💬 Telegram: @{seller.telegram_username or seller.telegram_id}\n\n"
        f"📝 О компании:\n{seller.description or 'Не указано'}\n"
    )
    
    # WebApp URL с параметром view
    # Используем прямой URL фронтенда, чтобы открыть именно нужную страницу
    # (Telegram откроет это внутри WebApp контейнера)
    webapp_url = "https://alert-joy-production.up.railway.app/admin?view=sellers"
    
    # Кнопка WebApp
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ Открыть Админку", web_app=WebAppInfo(url=webapp_url))]
    ])
    
    for admin_id in ADMIN_CHAT_IDS:
        try:
            await bot.send_message(admin_id, text, parse_mode="HTML", reply_markup=kb)
        except Exception as e:
            print(f"Failed to notify admin {admin_id}: {e}")


async def notify_seller_status_change(seller: models.Seller):
    """Уведомление продавцу об изменении статуса"""
    if not bot:
        return
    
    status_messages = {
        "approved": "✅ Ваша заявка на партнерство одобрена! Теперь вы можете добавлять товары.",
        "rejected": "❌ К сожалению, ваша заявка на партнерство отклонена.",
        "banned": "🚫 Ваш аккаунт продавца заблокирован.",
    }
    
    text = status_messages.get(seller.status, f"ℹ️ Статус вашей заявки изменен: {seller.status}")
    
    try:
        await bot.send_message(int(seller.telegram_id), text)
    except Exception as e:
        print(f"Failed to notify seller {seller.telegram_id}: {e}")


async def notify_listing_pending(listing: models.Listing):
    """Уведомление админу о новом объявлении на модерации"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
    
    if not bot or not ADMIN_CHAT_IDS:
        return
    
    text = (
        f"📦 <b>Новое объявление на модерации!</b>\n\n"
        f"📌 <b>{listing.title}</b>\n"
        f"💰 Цена: {listing.price:,.0f} ₽\n"
        f"📍 Город: {listing.city or 'Не указан'}\n"
        f"👤 Продавец: {listing.seller_name or 'Не указан'}\n"
        f"💬 Telegram: @{listing.seller_telegram_username or listing.seller_telegram_id}\n\n"
        f"📝 {listing.description[:200] if listing.description else 'Без описания'}..."
    )
    
    # WebApp URL с параметром view
    # Используем прямой URL фронтенда, чтобы открыть именно нужную страницу
    # (Telegram откроет это внутри WebApp контейнера)
    webapp_url = "https://alert-joy-production.up.railway.app/admin?view=listings"
    
    # Кнопка WebApp
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ Открыть Админку", web_app=WebAppInfo(url=webapp_url))]
    ])
    
    for admin_id in ADMIN_CHAT_IDS:
        try:
            await bot.send_message(admin_id, text, parse_mode="HTML", reply_markup=kb)
        except Exception as e:
            print(f"Failed to notify admin {admin_id}: {e}")


async def notify_listing_status_change(listing: models.Listing):
    """Уведомление продавцу об изменении статуса объявления"""
    if not bot:
        return
    
    status_messages = {
        "approved": f"✅ Ваше объявление «{listing.title}» одобрено и опубликовано!",
        "rejected": f"❌ Объявление «{listing.title}» отклонено. Причина: {listing.rejection_reason or 'Не указана'}",
        "sold": f"🎉 Объявление «{listing.title}» отмечено как проданное!",
    }
    
    text = status_messages.get(listing.status, f"ℹ️ Статус объявления изменен: {listing.status}")
    
    try:
        await bot.send_message(int(listing.seller_telegram_id), text)
    except Exception as e:
        print(f"Failed to notify listing seller {listing.seller_telegram_id}: {e}")

