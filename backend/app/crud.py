from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from . import models, schemas

# Product CRUD
async def get_product(db: AsyncSession, product_id: int):
    result = await db.execute(
        select(models.Product)
        .where(models.Product.id == product_id)
        .options(
            selectinload(models.Product.seller),
            selectinload(models.Product.category)  # Загружаем категорию!
        )
    )
    return result.scalars().first()

async def get_product_by_part_number(db: AsyncSession, part_number: str):
    result = await db.execute(
        select(models.Product)
        .where(models.Product.part_number == part_number)
        .options(
            selectinload(models.Product.seller),
            selectinload(models.Product.category)  # Загружаем категорию!
        )
    )
    return result.scalars().first()

async def get_products(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(
        select(models.Product)
        .options(
            selectinload(models.Product.seller),
            selectinload(models.Product.category)  # Загружаем категорию!
        )
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def create_product(db: AsyncSession, product: schemas.ProductCreate):
    db_product = models.Product(**product.model_dump())
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    return db_product

async def update_product(db: AsyncSession, product_id: int, product_update: schemas.ProductUpdate):
    """Обновить товар"""
    result = await db.execute(
        select(models.Product).where(models.Product.id == product_id)
    )
    db_product = result.scalars().first()
    
    if not db_product:
        return None
    
    # Обновляем только те поля, которые переданы (exclude_none вместо exclude_unset!)
    update_data = product_update.model_dump(exclude_none=True)
    
    # Но images может быть пустым массивом - это валидное значение!
    if product_update.images is not None:
        update_data['images'] = product_update.images
    
    print(f"🔧 update_data: {update_data}")
    
    for field, value in update_data.items():
        setattr(db_product, field, value)
    
    await db.commit()
    await db.refresh(db_product)
    return db_product

# Category CRUD
async def get_categories(db: AsyncSession):
    result = await db.execute(select(models.Category))
    return result.scalars().all()

async def create_category(db: AsyncSession, category: schemas.CategoryCreate):
    db_category = models.Category(**category.model_dump())
    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)
    return db_category







