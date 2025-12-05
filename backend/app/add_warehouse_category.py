import asyncio
from sqlalchemy import select
from app.database import SessionLocal
from app.models import Category
from slugify import slugify

async def add_warehouse_to_tree():
    async with SessionLocal() as db:
        # Проверяем, есть ли категория "Склад (New)"
        result = await db.execute(select(Category).where(Category.name == "Склад (New)"))
        warehouse = result.scalar_one_or_none()
        
        if warehouse:
            print(f"Найдена категория 'Склад (New)' с ID {warehouse.id}")
            
            # Проверяем, есть ли уже "Все товары" в корне
            result = await db.execute(select(Category).where(Category.name == "📦 Все товары со склада"))
            existing = result.scalar_one_or_none()
            
            if not existing:
                # Создаём новую корневую категорию, которая будет ссылаться на ID склада
                # Но так как товары уже в ID 50, просто переименуем существующую
                warehouse.name = "📦 Все товары со склада"
                warehouse.parent_id = None  # Делаем корневой
                await db.commit()
                print("✅ Категория обновлена и перемещена в корень")
            else:
                print("Категория уже существует")
        else:
            print("❌ Категория 'Склад (New)' не найдена")

if __name__ == "__main__":
    asyncio.run(add_warehouse_to_tree())



