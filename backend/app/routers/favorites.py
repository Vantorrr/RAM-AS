from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from typing import List, Optional
from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/favorites", tags=["Favorites"])

@router.post("/{product_id}/toggle")
async def toggle_favorite(
    product_id: int,
    user_telegram_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Добавить/удалить из избранного"""
    # Проверить существование товара
    product_res = await db.execute(select(models.Product).where(models.Product.id == product_id))
    product = product_res.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    # Проверить существование в избранном
    stmt = select(models.Favorite).where(
        models.Favorite.user_telegram_id == user_telegram_id,
        models.Favorite.product_id == product_id
    )
    result = await db.execute(stmt)
    favorite = result.scalar_one_or_none()
    
    if favorite:
        await db.delete(favorite)
        await db.commit()
        return {"status": "removed", "is_favorite": False}
    else:
        new_fav = models.Favorite(
            user_telegram_id=user_telegram_id,
            product_id=product_id
        )
        db.add(new_fav)
        await db.commit()
        return {"status": "added", "is_favorite": True}

@router.get("/", response_model=List[schemas.Product])
async def get_favorites(
    user_telegram_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Получить все избранные товары"""
    stmt = select(models.Product).join(models.Favorite).where(
        models.Favorite.user_telegram_id == user_telegram_id
    )
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/ids", response_model=List[int])
async def get_favorite_ids(
    user_telegram_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Получить ID всех избранных товаров (для подсветки сердечек)"""
    stmt = select(models.Favorite.product_id).where(
        models.Favorite.user_telegram_id == user_telegram_id
    )
    result = await db.execute(stmt)
    return result.scalars().all()

