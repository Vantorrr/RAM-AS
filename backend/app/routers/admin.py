"""
Admin API Router
Управление категориями, витриной и настройками магазина
"""

import os
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from pydantic import BaseModel

from .. import models, schemas
from ..database import get_db

# Список ID админов из переменной окружения
ADMIN_CHAT_IDS = os.getenv("ADMIN_CHAT_IDS", "").split(",")
ADMIN_CHAT_IDS = [x.strip() for x in ADMIN_CHAT_IDS if x.strip()]

def verify_admin(x_telegram_user_id: Optional[str] = Header(None)):
    """Проверка, что запрос от админа"""
    if not x_telegram_user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Missing Telegram User ID")
    
    if x_telegram_user_id not in ADMIN_CHAT_IDS:
        raise HTTPException(status_code=403, detail="Forbidden: Admin access required")
    
    return x_telegram_user_id

router = APIRouter(
    prefix="/api/admin", 
    tags=["Admin"],
    dependencies=[Depends(verify_admin)]  # Защита всех роутов!
)


# ============ КАТЕГОРИИ ============

@router.get("/categories", response_model=List[schemas.Category])
async def get_all_categories(db: AsyncSession = Depends(get_db)):
    """Получить все категории (плоский список)"""
    result = await db.execute(select(models.Category).order_by(models.Category.name))
    return result.scalars().all()


@router.get("/categories/tree")
async def get_categories_tree(db: AsyncSession = Depends(get_db)):
    """Получить дерево категорий"""
    # Загружаем все категории
    result = await db.execute(
        select(models.Category).order_by(models.Category.name)
    )
    all_categories = result.scalars().all()
    
    # Строим дерево вручную
    cat_dict = {}
    for cat in all_categories:
        cat_dict[cat.id] = {
            "id": cat.id,
            "name": cat.name,
            "slug": cat.slug,
            "image_url": cat.image_url,
            "parent_id": cat.parent_id,
            "children": []
        }
    
    # Собираем дерево
    root_cats = []
    for cat in all_categories:
        if cat.parent_id is None:
            root_cats.append(cat_dict[cat.id])
        elif cat.parent_id in cat_dict:
            cat_dict[cat.parent_id]["children"].append(cat_dict[cat.id])
    
    return root_cats


@router.post("/categories", response_model=schemas.Category)
async def create_category(
    category: schemas.CategoryCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создать категорию"""
    # Проверяем уникальность slug
    existing = await db.execute(
        select(models.Category).where(models.Category.slug == category.slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Категория с таким slug уже существует")
    
    db_category = models.Category(
        name=category.name,
        slug=category.slug,
        parent_id=category.parent_id,
        image_url=category.image_url
    )
    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)
    return db_category


@router.put("/categories/{category_id}", response_model=schemas.Category)
async def update_category(
    category_id: int,
    category_data: schemas.CategoryUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Обновить категорию"""
    result = await db.execute(
        select(models.Category).where(models.Category.id == category_id)
    )
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    
    # Проверяем slug на уникальность если меняется
    if category_data.slug and category_data.slug != category.slug:
        existing = await db.execute(
            select(models.Category).where(models.Category.slug == category_data.slug)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Категория с таким slug уже существует")
    
    # Обновляем только переданные поля
    if category_data.name is not None:
        category.name = category_data.name
    if category_data.slug is not None:
        category.slug = category_data.slug
    if category_data.parent_id is not None:
        category.parent_id = category_data.parent_id if category_data.parent_id != 0 else None
    if category_data.image_url is not None:
        category.image_url = category_data.image_url
    
    await db.commit()
    await db.refresh(category)
    return category


@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Удалить категорию"""
    result = await db.execute(
        select(models.Category).where(models.Category.id == category_id)
    )
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    
    # Проверяем есть ли товары в категории
    products_result = await db.execute(
        select(models.Product).where(models.Product.category_id == category_id).limit(1)
    )
    if products_result.scalar_one_or_none():
        raise HTTPException(
            status_code=400, 
            detail="Нельзя удалить категорию с товарами. Сначала переместите товары."
        )
    
    await db.delete(category)
    await db.commit()
    return {"status": "ok", "message": "Категория удалена"}


# ============ ВИТРИНА ============

class FeaturedProductRequest(BaseModel):
    product_id: int
    is_featured: bool
    display_order: Optional[int] = 0


@router.get("/showcase")
async def get_showcase_products(db: AsyncSession = Depends(get_db)):
    """Получить товары витрины"""
    result = await db.execute(
        select(models.Product)
        .where(models.Product.is_featured == True)
        .order_by(models.Product.display_order, models.Product.id)
    )
    products = result.scalars().all()
    
    return [{
        "id": p.id,
        "name": p.name,
        "part_number": p.part_number,
        "price_rub": p.price_rub,
        "image_url": p.image_url,
        "display_order": p.display_order,
        "is_featured": p.is_featured,
        "category_id": p.category_id
    } for p in products]


@router.post("/showcase/add")
async def add_to_showcase(
    request: FeaturedProductRequest,
    db: AsyncSession = Depends(get_db)
):
    """Добавить товар на витрину"""
    result = await db.execute(
        select(models.Product).where(models.Product.id == request.product_id)
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    product.is_featured = request.is_featured
    product.display_order = request.display_order
    
    await db.commit()
    return {"status": "ok", "message": "Товар обновлён на витрине"}


@router.post("/showcase/reorder")
async def reorder_showcase(
    products: List[dict],  # [{"id": 1, "display_order": 0}, ...]
    db: AsyncSession = Depends(get_db)
):
    """Изменить порядок товаров на витрине"""
    for item in products:
        result = await db.execute(
            select(models.Product).where(models.Product.id == item["id"])
        )
        product = result.scalar_one_or_none()
        if product:
            product.display_order = item.get("display_order", 0)
    
    await db.commit()
    return {"status": "ok", "message": "Порядок обновлён"}


@router.delete("/showcase/{product_id}")
async def remove_from_showcase(
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Убрать товар с витрины"""
    result = await db.execute(
        select(models.Product).where(models.Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    product.is_featured = False
    product.display_order = 0
    
    await db.commit()
    return {"status": "ok", "message": "Товар убран с витрины"}


# ============ СТАТИСТИКА ============

@router.get("/stats")
async def get_admin_stats(db: AsyncSession = Depends(get_db)):
    """Общая статистика для админки"""
    from sqlalchemy import func
    
    # Количество товаров
    products_count = await db.execute(select(func.count(models.Product.id)))
    
    # Количество категорий
    categories_count = await db.execute(select(func.count(models.Category.id)))
    
    # Количество заказов
    orders_count = await db.execute(select(func.count(models.Order.id)))
    
    # Количество партнеров
    sellers_count = await db.execute(select(func.count(models.Seller.id)))
    
    # Товары на витрине
    featured_count = await db.execute(
        select(func.count(models.Product.id)).where(models.Product.is_featured == True)
    )
    
    return {
        "total_products": products_count.scalar(),
        "total_categories": categories_count.scalar(),
        "total_orders": orders_count.scalar(),
        "total_sellers": sellers_count.scalar(),
        "featured_products": featured_count.scalar()
    }

