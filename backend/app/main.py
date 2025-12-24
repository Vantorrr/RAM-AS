import asyncio
import os
import uuid
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqladmin import Admin, ModelView
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from . import models, schemas, crud, database, currency
from .database import engine, sync_engine
from .bot import notify_new_order
from .routers import marketplace, ai, favorites, payments, cdek, vehicles
from .routers import admin as admin_router

# Create uploads directory
# Используем Railway Volume для хранения файлов
# В продакшене /data — это примонтированный Volume
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/data/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
print(f"📁 Upload directory: {UPLOAD_DIR}")

app = FastAPI(
    title="RAM US Auto Parts",
    description="API for Telegram WebApp Auto Parts Store",
    version="0.1.0"
)

# CORS Configuration
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://alert-joy-production.up.railway.app",
    "https://ram-us-webapp.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for WebApp
    allow_credentials=False,  # Disable credentials for wildcard
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for uploads
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Admin Views
class ProductAdmin(ModelView, model=models.Product):
    name = "Товар"
    name_plural = "Товары"
    icon = "fa-solid fa-box"
    
    # Колонки в списке
    column_list = [
        models.Product.id, 
        models.Product.name, 
        models.Product.part_number,
        models.Product.price_rub, 
        models.Product.is_in_stock,
        models.Product.stock_quantity,
        models.Product.is_installment_available,
        models.Product.category_id,
    ]
    
    # Поля для редактирования
    form_columns = [
        models.Product.name,
        models.Product.part_number,
        models.Product.description,
        models.Product.manufacturer,
        models.Product.price_rub,
        models.Product.price_usd,
        models.Product.is_in_stock,
        models.Product.stock_quantity,
        models.Product.image_url,
        models.Product.is_preorder,
        models.Product.is_installment_available,
        models.Product.category_id,
        models.Product.vehicles,  # Добавлено поле для выбора машин
    ]
    
    # Поиск
    column_searchable_list = [models.Product.name, models.Product.part_number, models.Product.description]
    
    # Сортировка
    column_sortable_list = [
        models.Product.id,
        models.Product.name,
        models.Product.price_rub, 
        models.Product.is_in_stock,
        models.Product.stock_quantity,
    ]
    
    # Фильтры
    column_default_sort = [(models.Product.id, True)]
    
    # Подсказки
    form_args = {
        "name": {"label": "Название товара"},
        "part_number": {"label": "Артикул"},
        "description": {"label": "Описание"},
        "manufacturer": {"label": "Производитель"},
        "price_rub": {"label": "Цена (₽)"},
        "price_usd": {"label": "Цена ($)"},
        "is_in_stock": {"label": "В наличии"},
        "stock_quantity": {"label": "Кол-во на складе"},
        "image_url": {"label": "URL фото"},
        "is_preorder": {"label": "Под заказ"},
        "is_installment_available": {"label": "Рассрочка 0%"},
        "category_id": {"label": "Категория (ID)"},
        "vehicles": {"label": "Совместимость с авто"},
    }
    
    # Настройка ajax для vehicles, если записей много
    form_ajax_refs = {
        "vehicles": {
            "fields": ["make", "model", "generation", "engine"],
            "placeholder": "Выберите автомобиль",
            "page_size": 10,
            "minimum_input_length": 0,
        }
    }

class CategoryAdmin(ModelView, model=models.Category):
    name = "Категория"
    name_plural = "Категории"
    icon = "fa-solid fa-folder"
    
    column_list = [
        models.Category.id, 
        models.Category.name, 
        models.Category.slug,
        models.Category.parent_id,
        models.Category.image_url
    ]
    
    form_columns = [
        models.Category.name,
        models.Category.slug,
        models.Category.parent_id,
        models.Category.image_url,
    ]
    
    column_searchable_list = [models.Category.name]
    column_sortable_list = [models.Category.id, models.Category.name, models.Category.parent_id]
    
    form_args = {
        "name": {"label": "Название"},
        "slug": {"label": "URL (slug)"},
        "parent_id": {"label": "Родительская категория (ID)"},
        "image_url": {"label": "URL картинки"},
    }

class OrderAdmin(ModelView, model=models.Order):
    name = "Заказ"
    name_plural = "Заказы"
    icon = "fa-solid fa-cart-shopping"
    
    column_list = [
        models.Order.id, 
        models.Order.user_telegram_id, 
        models.Order.user_name,
        models.Order.user_phone,
        models.Order.total_amount, 
        models.Order.status,
        models.Order.created_at,
    ]
    
    form_columns = [
        models.Order.user_telegram_id,
        models.Order.user_name,
        models.Order.user_phone,
        models.Order.delivery_address,
        models.Order.total_amount,
        models.Order.status,
    ]
    
    column_sortable_list = [models.Order.id, models.Order.total_amount, models.Order.created_at]
    column_default_sort = [(models.Order.id, True)]
    
    form_args = {
        "user_telegram_id": {"label": "Telegram ID"},
        "user_name": {"label": "Имя клиента"},
        "user_phone": {"label": "Телефон"},
        "delivery_address": {"label": "Адрес доставки"},
        "total_amount": {"label": "Сумма (₽)"},
        "status": {"label": "Статус"},
    }

class VehicleAdmin(ModelView, model=models.Vehicle):
    name = "Автомобиль"
    name_plural = "🚘 Автомобили (Fitment)"
    icon = "fa-solid fa-car"
    
    column_list = [
        models.Vehicle.id, 
        models.Vehicle.make, 
        models.Vehicle.model, 
        models.Vehicle.generation, 
        models.Vehicle.year_from,
        models.Vehicle.year_to,
        models.Vehicle.engine
    ]
    
    column_sortable_list = [models.Vehicle.make, models.Vehicle.model]
    column_searchable_list = [models.Vehicle.make, models.Vehicle.model, models.Vehicle.generation, models.Vehicle.engine]
    
    form_columns = [
        models.Vehicle.make, 
        models.Vehicle.model, 
        models.Vehicle.generation, 
        models.Vehicle.year_from, 
        models.Vehicle.year_to, 
        models.Vehicle.engine
    ]
    
    form_args = {
        "make": {"label": "Марка (RAM, Dodge)"},
        "model": {"label": "Модель (1500, TRX)"},
        "generation": {"label": "Поколение (DT, DS)"},
        "year_from": {"label": "Год начала"},
        "year_to": {"label": "Год окончания (пусто если н.в.)"},
        "engine": {"label": "Двигатель (5.7L HEMI)"},
    }

# ============ MARKETPLACE ADMIN ============

class SellerAdmin(ModelView, model=models.Seller):
    name = "Партнер"
    name_plural = "🤝 Партнеры"
    icon = "fa-solid fa-handshake"
    
    column_list = [
        models.Seller.id,
        models.Seller.name,
        models.Seller.telegram_username,
        models.Seller.status,
        models.Seller.is_verified,
        models.Seller.subscription_tier,
        models.Seller.max_products,
        models.Seller.created_at,
    ]
    
    form_columns = [
        models.Seller.name,
        models.Seller.contact_name,
        models.Seller.phone,
        models.Seller.email,
        models.Seller.telegram_id,
        models.Seller.telegram_username,
        models.Seller.description,
        models.Seller.logo_url,
        models.Seller.status,
        models.Seller.is_verified,
        models.Seller.subscription_tier,
        models.Seller.subscription_expires,
        models.Seller.max_products,
    ]
    
    # Виджеты для редактирования (чтобы было удобно)
    form_args = {
        "status": {
            "label": "Статус аккаунта",
            "choices": [
                ("pending", "Ожидает (Pending)"),
                ("approved", "Одобрен (Approved)"),
                ("rejected", "Отклонен (Rejected)"),
                ("banned", "Заблокирован (Banned)")
            ]
        },
        "subscription_tier": {
            "label": "Тариф подписки",
            "choices": [
                ("free", "Бесплатный (Free) - 10 товаров"),
                ("start", "Старт (Start) - 50 товаров"),
                ("pro", "Профи (Pro) - 1000 товаров"),
                ("magnate", "Магнат (Magnate) - Безлимит")
            ]
        },
        "is_verified": {"label": "Галочка 'Проверенный партнер'"},
        "max_products": {"label": "Лимит товаров (шт)"},
        "subscription_expires": {"label": "Дата окончания подписки"}
    }


class ListingAdmin(ModelView, model=models.Listing):
    name = "Объявление"
    name_plural = "🏷️ Барахолка"
    icon = "fa-solid fa-tag"
    
    column_list = [
        models.Listing.id,
        models.Listing.title,
        models.Listing.price,
        models.Listing.city,
        models.Listing.status,
        models.Listing.is_paid,
        models.Listing.is_promoted,
        models.Listing.views_count,
        models.Listing.created_at,
    ]
    
    form_columns = [
        models.Listing.title,
        models.Listing.description,
        models.Listing.price,
        models.Listing.city,
        models.Listing.images,
        models.Listing.seller_name,
        models.Listing.seller_phone,
        models.Listing.seller_telegram_id,
        models.Listing.seller_telegram_username,
        models.Listing.status,
        models.Listing.rejection_reason,
        models.Listing.is_paid,
        models.Listing.payment_amount,
        models.Listing.is_promoted,
        models.Listing.promoted_until,
        models.Listing.expires_at,
    ]
    
    column_searchable_list = [models.Listing.title, models.Listing.seller_name, models.Listing.city]
    column_sortable_list = [models.Listing.id, models.Listing.price, models.Listing.status, models.Listing.created_at]
    column_default_sort = [(models.Listing.id, True)]
    
    form_args = {
        "title": {"label": "Заголовок"},
        "description": {"label": "Описание"},
        "price": {"label": "Цена (₽)"},
        "city": {"label": "Город"},
        "images": {"label": "Фото (JSON)"},
        "seller_name": {"label": "Имя продавца"},
        "seller_phone": {"label": "Телефон продавца"},
        "seller_telegram_id": {"label": "Telegram ID"},
        "seller_telegram_username": {"label": "Telegram @username"},
        "status": {"label": "Статус (draft/pending/approved/rejected/sold)"},
        "rejection_reason": {"label": "Причина отклонения"},
        "is_paid": {"label": "Оплачено"},
        "payment_amount": {"label": "Сумма оплаты"},
        "is_promoted": {"label": "Продвигается"},
        "promoted_until": {"label": "Продвижение до"},
        "expires_at": {"label": "Истекает"},
    }

# SQLAdmin setup (используем SYNC engine, т.к. sqladmin не поддерживает async полностью)
print(f"🔧 Setting up SQLAdmin...")
print(f"🔧 Sync Engine: {sync_engine}")
admin = Admin(app, sync_engine)
print(f"🔧 Admin created, adding views...")
admin.add_view(ProductAdmin)
print(f"✅ Added ProductAdmin")
admin.add_view(CategoryAdmin)
print(f"✅ Added CategoryAdmin")
admin.add_view(OrderAdmin)
print(f"✅ Added OrderAdmin")
admin.add_view(VehicleAdmin)
print(f"✅ Added VehicleAdmin")
admin.add_view(SellerAdmin)
print(f"✅ Added SellerAdmin")
admin.add_view(ListingAdmin)
print(f"✅ Added ListingAdmin")
print(f"🎉 SQLAdmin setup complete!")

# Include Marketplace Router
app.include_router(marketplace.router)
app.include_router(ai.router)
app.include_router(favorites.router)
app.include_router(payments.router)
app.include_router(cdek.router)
app.include_router(vehicles.router)
app.include_router(admin_router.router)

@app.post("/system/auto-link-products")
async def auto_link_products(db: AsyncSession = Depends(database.get_db)):
    """
    ВРЕМЕННЫЙ ЭНДПОИНТ: Автоматическая привязка товаров к машинам
    """
    import re
    
    print("🚀 Начинаю автоматическую привязку товаров к машинам...")
    
    # Получаем все товары и машины
    products_result = await db.execute(select(models.Product))
    products = products_result.scalars().all()
    
    vehicles_result = await db.execute(select(models.Vehicle))
    vehicles = vehicles_result.scalars().all()
    
    print(f"📦 Товаров: {len(products)}")
    print(f"🚗 Машин: {len(vehicles)}")
    
    # Группируем машины по маркам
    vehicles_by_make = {}
    for v in vehicles:
        if v.make not in vehicles_by_make:
            vehicles_by_make[v.make] = []
        vehicles_by_make[v.make].append(v)
    
    # Универсальные категории
    UNIVERSAL_KEYWORDS = [
        'масло', 'жидкость', 'антифриз', 'тосол', 'омывайка', 
        'аксессуар', 'ароматизатор', 'коврик', 'чехол', 'органайзер',
        'держатель', 'зарядное', 'usb', 'видеорегистратор', 'радар',
        'компрессор', 'насос', 'инструмент', 'ключ', 'домкрат',
        'трос', 'аптечка', 'огнетушитель', 'знак', 'жилет',
        'щетка', 'скребок', 'губка', 'салфетка', 'полироль',
        'шампунь', 'воск', 'полотенце', 'перчатки', 'маска',
    ]
    
    def is_universal(product_name):
        text = product_name.lower()
        return any(keyword in text for keyword in UNIVERSAL_KEYWORDS)
    
    def get_matching_makes(product_name):
        text = product_name.lower()
        matches = []
        
        if any(word in text for word in ['ram', 'рам', 'dodge', 'додж', 'jeep', 'джип', 'hemi', 'хеми', 'trx']):
            matches.extend(['RAM', 'Dodge', 'Jeep'])
        if any(word in text for word in ['bmw', 'бмв']):
            matches.append('BMW')
        if any(word in text for word in ['mercedes', 'мерседес', 'benz', 'бенц']):
            matches.append('Mercedes-Benz')
        if any(word in text for word in ['audi', 'ауди']):
            matches.append('Audi')
        if any(word in text for word in ['toyota', 'тойота', 'camry', 'камри', 'land cruiser', 'крузер']):
            matches.append('Toyota')
        if any(word in text for word in ['lada', 'лада', 'ваз', 'granta', 'гранта', 'vesta', 'веста']):
            matches.append('Lada')
        if any(word in text for word in ['volkswagen', 'vw', 'фольксваген', 'polo', 'поло']):
            matches.append('Volkswagen')
        if any(word in text for word in ['hyundai', 'хендай', 'solaris', 'солярис', 'creta', 'крета']):
            matches.append('Hyundai')
        if any(word in text for word in ['kia', 'киа', 'rio', 'рио']):
            matches.append('Kia')
        
        return list(set(matches))
    
    linked_count = 0
    universal_count = 0
    specific_count = 0
    
    for product in products:
        # Очищаем старые связи через raw SQL
        from sqlalchemy import delete
        await db.execute(
            delete(models.product_vehicles).where(models.product_vehicles.c.product_id == product.id)
        )
        
        # Проверяем универсальность
        if is_universal(product.name):
            # Привязываем ко ВСЕМ машинам
            for vehicle in vehicles:
                from sqlalchemy import insert
                await db.execute(
                    insert(models.product_vehicles).values(
                        product_id=product.id,
                        vehicle_id=vehicle.id
                    )
                )
            universal_count += 1
            print(f"🌍 {product.name} → ВСЕ {len(vehicles)} машин")
        else:
            # Определяем конкретные марки
            matching_makes = get_matching_makes(product.name)
            
            if matching_makes:
                matched_vehicles = []
                for make in matching_makes:
                    if make in vehicles_by_make:
                        matched_vehicles.extend(vehicles_by_make[make])
                
                for vehicle in matched_vehicles:
                    from sqlalchemy import insert
                    await db.execute(
                        insert(models.product_vehicles).values(
                            product_id=product.id,
                            vehicle_id=vehicle.id
                        )
                    )
                specific_count += 1
                print(f"🎯 {product.name} → {matching_makes} ({len(matched_vehicles)} моделей)")
            else:
                # Если не определили - привязываем ко всем
                for vehicle in vehicles:
                    from sqlalchemy import insert
                    await db.execute(
                        insert(models.product_vehicles).values(
                            product_id=product.id,
                            vehicle_id=vehicle.id
                        )
                    )
                universal_count += 1
                print(f"❓ {product.name} → всем (не определено)")
        
        linked_count += 1
    
    await db.commit()
    
    return {
        "status": "success",
        "message": "Товары успешно привязаны к машинам!",
        "stats": {
            "total_products": linked_count,
            "universal": universal_count,
            "specific": specific_count,
            "total_vehicles": len(vehicles)
        }
    }

@app.on_event("startup")
async def startup():
    from sqlalchemy import text
    
    print("🚀 Starting database initialization...")
    
    async with engine.begin() as conn:
        # Create ALL tables (including marketplace: sellers, listings, subscriptions, vehicles)
        print("📊 Creating database tables...")
        await conn.run_sync(models.Base.metadata.create_all)
        print("✅ All tables created/verified")
        
        # Add missing columns (migrations for existing deployments)
        try:
            await conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS seller_id INTEGER REFERENCES sellers(id)"))
            print("✅ Added seller_id column to products")
        except Exception as e:
            print(f"⚠️ seller_id column: {e}")
        
        try:
            await conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS views_count INTEGER DEFAULT 0"))
            print("✅ Added views_count column to products")
        except Exception as e:
            print(f"⚠️ views_count column: {e}")
        
        # Витрина: новые колонки для featured товаров
        try:
            await conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS is_featured BOOLEAN DEFAULT FALSE"))
            print("✅ Added is_featured column to products")
        except Exception as e:
            print(f"⚠️ is_featured column: {e}")
        
        try:
            await conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS display_order INTEGER DEFAULT 0"))
            print("✅ Added display_order column to products")
        except Exception as e:
            print(f"⚠️ display_order column: {e}")
        
        # Миграции для категорий
        try:
            await conn.execute(text("ALTER TABLE categories ADD COLUMN IF NOT EXISTS parent_id INTEGER REFERENCES categories(id)"))
            print("✅ Added parent_id column to categories")
        except Exception as e:
            print(f"⚠️ parent_id column: {e}")
        
        try:
            await conn.execute(text("ALTER TABLE categories ADD COLUMN IF NOT EXISTS image_url VARCHAR"))
            print("✅ Added image_url column to categories")
        except Exception as e:
            print(f"⚠️ image_url column: {e}")
        
        # Миграции для СДЭК доставки в orders
        cdek_columns = [
            ("delivery_type", "VARCHAR"),
            ("delivery_cost", "FLOAT DEFAULT 0"),
            ("cdek_city_code", "INTEGER"),
            ("cdek_city_name", "VARCHAR"),
            ("cdek_pvz_code", "VARCHAR"),
            ("cdek_pvz_address", "VARCHAR"),
            ("cdek_tariff_code", "INTEGER"),
            ("cdek_uuid", "VARCHAR"),
            ("cdek_number", "VARCHAR"),
        ]
        for col_name, col_type in cdek_columns:
            try:
                await conn.execute(text(f"ALTER TABLE orders ADD COLUMN IF NOT EXISTS {col_name} {col_type}"))
            except Exception:
                pass
        print("✅ Added CDEK columns to orders")
    
    print("✅ Database ready!")
    
    # Start bot polling in background
    from .bot import bot, dp, ADMIN_CHAT_IDS, WEBAPP_URL
    if bot:
        print(f"🤖 Starting Telegram bot...")
        print(f"📋 Admins: {ADMIN_CHAT_IDS}")
        print(f"🌐 WebApp: {WEBAPP_URL}")
        
        # Настройка логирования для aiogram
        import logging
        logging.basicConfig(level=logging.INFO)
        
        asyncio.create_task(dp.start_polling(bot, skip_updates=False))

@app.get("/")
async def root():
    return {"message": "RAM US Auto Parts API is running. Stay Top."}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/products/", response_model=schemas.Product)
async def create_product(product: schemas.ProductCreate, db: AsyncSession = Depends(database.get_db)):
    db_product = await crud.get_product_by_part_number(db, part_number=product.part_number)
    if db_product:
        raise HTTPException(status_code=400, detail="Product with this part number already exists")
    return await crud.create_product(db=db, product=product)

async def get_all_subcategory_ids(db: AsyncSession, category_id: int) -> List[int]:
    """Получить все ID подкатегорий рекурсивно"""
    result = await db.execute(
        select(models.Category.id).where(models.Category.parent_id == category_id)
    )
    child_ids = [row[0] for row in result.fetchall()]
    
    all_ids = [category_id]
    for child_id in child_ids:
        all_ids.extend(await get_all_subcategory_ids(db, child_id))
    
    return all_ids

@app.get("/products/", response_model=List[schemas.Product])
async def read_products(
    skip: int = 0, 
    limit: int = 100, 
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock: Optional[bool] = None,
    vehicle_make: Optional[str] = None,
    vehicle_model: Optional[str] = None,
    vehicle_year: Optional[int] = None,
    vehicle_engine: Optional[str] = None,
    sort_by: Optional[str] = None,  # price_asc, price_desc, name_asc, name_desc
    db: AsyncSession = Depends(database.get_db)
):
    query = select(models.Product).options(selectinload(models.Product.seller))
    
    # Фильтр по авто
    if vehicle_make or vehicle_model:
        query = query.join(models.Product.vehicles)
        
        if vehicle_make:
            query = query.where(models.Vehicle.make == vehicle_make)
        if vehicle_model:
            query = query.where(models.Vehicle.model == vehicle_model)
        if vehicle_engine:
            query = query.where(models.Vehicle.engine == vehicle_engine)
        if vehicle_year:
            # Год должен попадать в диапазон выпуска авто
            query = query.where(
                (models.Vehicle.year_from <= vehicle_year) & 
                ((models.Vehicle.year_to == None) | (models.Vehicle.year_to >= vehicle_year))
            )
        
        # Убираем дубликаты, если товар подходит к нескольким подходящим машинам
        query = query.distinct()
    
    if category_id:
        # Получаем все подкатегории рекурсивно
        all_category_ids = await get_all_subcategory_ids(db, category_id)
        query = query.where(models.Product.category_id.in_(all_category_ids))
    
    if search:
        search_filter = f"%{search}%"
        query = query.where(
            (models.Product.name.ilike(search_filter)) |
            (models.Product.part_number.ilike(search_filter)) |
            (models.Product.manufacturer.ilike(search_filter))
        )
    
    if min_price is not None:
        query = query.where(models.Product.price_rub >= min_price)
    
    if max_price is not None:
        query = query.where(models.Product.price_rub <= max_price)
    
    if in_stock is not None:
        query = query.where(models.Product.is_in_stock == in_stock)
    
    # Сортировка
    if sort_by == "price_asc":
        query = query.order_by(models.Product.price_rub.asc())
    elif sort_by == "price_desc":
        query = query.order_by(models.Product.price_rub.desc())
    elif sort_by == "name_asc":
        query = query.order_by(models.Product.name.asc())
    elif sort_by == "name_desc":
        query = query.order_by(models.Product.name.desc())
        
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@app.get("/products/featured", response_model=List[schemas.Product])
async def get_featured_products(
    limit: int = 8,
    db: AsyncSession = Depends(database.get_db)
):
    """Получить товары витрины (is_featured=True)"""
    result = await db.execute(
        select(models.Product)
        .options(selectinload(models.Product.seller))
        .where(models.Product.is_featured == True)
        .order_by(models.Product.display_order, models.Product.id)
        .limit(limit)
    )
    return result.scalars().all()


@app.get("/products/count")
async def get_products_count(
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock: Optional[bool] = None,
    vehicle_make: Optional[str] = None,
    vehicle_model: Optional[str] = None,
    vehicle_year: Optional[int] = None,
    vehicle_engine: Optional[str] = None,
    db: AsyncSession = Depends(database.get_db)
):
    from sqlalchemy import func
    query = select(func.count(models.Product.id))
    
    # Фильтр по авто (нужен join для count тоже, если фильтруем)
    if vehicle_make or vehicle_model:
        query = select(func.count(distinct(models.Product.id))).join(models.Product.vehicles)
        
        if vehicle_make:
            query = query.where(models.Vehicle.make == vehicle_make)
        if vehicle_model:
            query = query.where(models.Vehicle.model == vehicle_model)
        if vehicle_engine:
            query = query.where(models.Vehicle.engine == vehicle_engine)
        if vehicle_year:
            query = query.where(
                (models.Vehicle.year_from <= vehicle_year) & 
                ((models.Vehicle.year_to == None) | (models.Vehicle.year_to >= vehicle_year))
            )
    
    if category_id:
        # Получаем все подкатегории рекурсивно
        all_category_ids = await get_all_subcategory_ids(db, category_id)
        query = query.where(models.Product.category_id.in_(all_category_ids))
    
    if search:
        search_filter = f"%{search}%"
        query = query.where(
            (models.Product.name.ilike(search_filter)) |
            (models.Product.part_number.ilike(search_filter)) |
            (models.Product.manufacturer.ilike(search_filter))
        )
    
    if min_price is not None:
        query = query.where(models.Product.price_rub >= min_price)
    
    if max_price is not None:
        query = query.where(models.Product.price_rub <= max_price)
    
    if in_stock is not None:
        query = query.where(models.Product.is_in_stock == in_stock)
    
    result = await db.execute(query)
    return {"count": result.scalar()}

@app.get("/products/{product_id}", response_model=schemas.Product)
async def read_product(product_id: int, db: AsyncSession = Depends(database.get_db)):
    db_product = await crud.get_product(db, product_id=product_id)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

@app.put("/products/{product_id}", response_model=schemas.Product)
async def update_product(product_id: int, product_data: schemas.ProductUpdate, db: AsyncSession = Depends(database.get_db)):
    """Обновить товар (для админки)"""
    result = await db.execute(select(models.Product).where(models.Product.id == product_id))
    db_product = result.scalar_one_or_none()
    
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Update fields
    update_data = product_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(db_product, field):
            setattr(db_product, field, value)
    
    await db.commit()
    await db.refresh(db_product)
    return db_product

@app.post("/upload/image")
async def upload_image(file: UploadFile = File(...)):
    """Загрузить изображение товара"""
    # Проверяем тип файла
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Генерируем уникальное имя файла
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    # Сохраняем файл
    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Возвращаем URL
    # В продакшене это будет полный URL
    base_url = os.getenv("BASE_URL", "https://ram-as-production.up.railway.app")
    image_url = f"{base_url}/uploads/{filename}"
    
    return {"url": image_url, "filename": filename}


@app.post("/upload/")
async def upload_multiple_images(files: List[UploadFile] = File(...)):
    """Загрузить несколько изображений (до 5 штук)"""
    if len(files) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 files allowed")
    
    base_url = os.getenv("BASE_URL", "https://ram-as-production.up.railway.app")
    urls = []
    
    for file in files:
        # Проверяем тип файла
        if not file.content_type.startswith("image/"):
            continue
        
        # Генерируем уникальное имя файла
        ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        filename = f"{uuid.uuid4()}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        
        # Сохраняем файл
        with open(filepath, "wb") as f:
            content = await file.read()
            f.write(content)
        
        urls.append(f"{base_url}/uploads/{filename}")
    
    return {"urls": urls, "count": len(urls)}

@app.get("/categories/tree", response_model=List[schemas.CategoryTree])
async def get_categories_tree(db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(models.Category))
    categories = result.scalars().all()
    
    # Строим словарь категорий вручную, без from_orm
    cat_dict = {}
    for cat in categories:
        cat_dict[cat.id] = schemas.CategoryTree(
            id=cat.id,
            name=cat.name,
            slug=cat.slug,
            parent_id=cat.parent_id,
            image_url=cat.image_url,
            children=[]
        )
    
    root_cats = []
    
    for cat in categories:
        if cat.parent_id is None:
            root_cats.append(cat_dict[cat.id])
        else:
            if cat.parent_id in cat_dict:
                cat_dict[cat.parent_id].children.append(cat_dict[cat.id])
                
    return root_cats

@app.get("/currency/usd-rate")
async def get_usd_rate():
    """Получить текущий курс USD/RUB"""
    rate = await currency.get_usd_rate()
    return {"rate": rate, "currency": "USD/RUB"}

@app.get("/orders/", response_model=List[schemas.Order])
async def get_all_orders(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(database.get_db)
):
    """Получить все заказы (для админки)"""
    result = await db.execute(
        select(models.Order)
        .order_by(models.Order.created_at.desc())
        .offset(skip)
        .limit(limit)
        .options(selectinload(models.Order.items).selectinload(models.OrderItem.product))
    )
    return result.scalars().all()

@app.get("/orders/count")
async def get_orders_count(db: AsyncSession = Depends(database.get_db)):
    """Получить количество заказов"""
    from sqlalchemy import func
    result = await db.execute(select(func.count(models.Order.id)))
    count = result.scalar()
    return {"count": count}

@app.get("/orders/user/{user_telegram_id}", response_model=List[schemas.Order])
async def get_user_orders(user_telegram_id: str, db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(
        select(models.Order)
        .where(models.Order.user_telegram_id == user_telegram_id)
        .order_by(models.Order.created_at.desc())
        .options(selectinload(models.Order.items).selectinload(models.OrderItem.product))
    )
    return result.scalars().all()

@app.post("/orders/", response_model=schemas.Order)
async def create_order(
    order: schemas.OrderCreate, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(database.get_db)
):
    """Создать новый заказ"""
    db_order = models.Order(
        user_telegram_id=order.user_telegram_id,
        user_name=order.user_name,
        user_phone=order.user_phone,
        delivery_address=order.delivery_address,
        total_amount=order.total_amount,
        status="pending",
        # СДЭК доставка
        delivery_type=order.delivery_type,
        delivery_cost=order.delivery_cost or 0,
        cdek_city_code=order.cdek_city_code,
        cdek_city_name=order.cdek_city_name,
        cdek_pvz_code=order.cdek_pvz_code,
        cdek_pvz_address=order.cdek_pvz_address,
        cdek_tariff_code=order.cdek_tariff_code,
    )
    db.add(db_order)
    await db.flush()
    
    # Сохраняем ID сразу после flush, пока объект еще не expired
    order_id = db_order.id
    
    # Добавляем товары в заказ
    for item in order.items:
        db_item = models.OrderItem(
            order_id=order_id,
            product_id=item.product_id,
            quantity=item.quantity,
            price_at_purchase=item.price_at_purchase
        )
        db.add(db_item)
    
    await db.commit()
    
    # Загружаем заказ с items и products
    result = await db.execute(
        select(models.Order)
        .where(models.Order.id == order_id)
        .options(selectinload(models.Order.items).selectinload(models.OrderItem.product))
    )
    db_order = result.scalar_one()
    
    # Отправляем уведомление в фоне
    background_tasks.add_task(
        notify_new_order,
        {
            "id": db_order.id,
            "user_name": db_order.user_name,
            "user_phone": db_order.user_phone,
            "delivery_address": db_order.delivery_address,
            "total_amount": db_order.total_amount,
            "items": order.items,
            "created_at": db_order.created_at.strftime("%d.%m.%Y %H:%M")
        }
    )
    
    return db_order
