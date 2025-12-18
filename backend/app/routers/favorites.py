from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/favorites", tags=["Favorites"])

@router.post("/", response_model=schemas.Favorite)
async def add_favorite(
    favorite_create: schemas.FavoriteCreate,
    db: AsyncSession = Depends(get_db)
):
    """Добавить товар в избранное"""
    # Проверяем, существует ли уже такой избранный товар для пользователя
    existing_favorite = await db.execute(
        select(models.Favorite)
        .where(models.Favorite.user_telegram_id == favorite_create.user_telegram_id)
        .where(models.Favorite.product_id == favorite_create.product_id)
    )
    if existing_favorite.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Товар уже в избранном")
    
    # Проверяем, существует ли товар
    product_exists = await db.execute(
        select(models.Product.id).where(models.Product.id == favorite_create.product_id)
    )
    if not product_exists.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Товар не найден")

    db_favorite = models.Favorite(**favorite_create.model_dump())
    db.add(db_favorite)
    await db.commit()
    await db.refresh(db_favorite)
    return db_favorite

@router.get("/{user_telegram_id}", response_model=List[schemas.Product])
async def get_favorites(
    user_telegram_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Получить все избранные товары пользователя"""
    result = await db.execute(
        select(models.Favorite)
        .where(models.Favorite.user_telegram_id == user_telegram_id)
        .options(selectinload(models.Favorite.product))
    )
    favorites = result.scalars().all()
    return [fav.product for fav in favorites if fav.product]

@router.delete("/{user_telegram_id}/{product_id}")
async def remove_favorite(
    user_telegram_id: str,
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Удалить товар из избранного"""
    result = await db.execute(
        select(models.Favorite)
        .where(models.Favorite.user_telegram_id == user_telegram_id)
        .where(models.Favorite.product_id == product_id)
    )
    favorite = result.scalar_one_or_none()
    
    if not favorite:
        raise HTTPException(status_code=404, detail="Товар не найден в избранном")
    
    await db.delete(favorite)
    await db.commit()
    return {"message": "Товар удален из избранного"}


