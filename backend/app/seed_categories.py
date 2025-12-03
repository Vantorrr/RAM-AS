import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from slugify import slugify

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import models
from app.database import DATABASE_URL

CATEGORIES_TREE = {
    "Детали для ТО": [
        "Фильтр масляный",
        "Фильтр воздушный",
        "Фильтр салонный",
        "Фильтр трансмиссионный, фильтр ГУР",
        "Свечи зажигания",
        "Ремень приводной",
        "Насос системы охлаждения",
        "Термостат",
        "Колодки тормозные",
        "Пробка сливного отверстия",
        "Щетки стеклоочистителя"
    ],
    "Двигатель": [],
    "Топливная система": [],
    "Система охлаждения": [],
    "Система выпуска": [],
    "Трансмиссия": [],
    "Ходовая часть": [],
    "Рулевое управление": [],
    "Тормозная система": [],
    "Электрооборудование": [],
    "Отопление / кондиционирование": [],
    "Детали салона": [
        "Панель приборов",
        "Подлокотник",
        "Подъемное устройство для окон",
        "Коврики",
        "Упругие элементы",
        "Ручки",
        "Органы управления автомобилем",
        "Вещевой ящик",
        "Центральная консоль",
        "Сидения",
        "Солнцезащитный козырёк",
        "Облицовка",
        {
            "Замок": [
                "Центральный замок",
                "Дистанционное управление, центральный замок",
                "Внешний замок",
                "Внутренний замок",
                "Комплект замков",
                "Цилиндр замка",
                "Ручки"
            ]
        }
    ],
    "Детали кузова": [],
    "Дополнительное оборудование": [],
    "Тюнинг": [
        "Фаркопы и крепления",
        "Системы холодного впуска",
        "Освещение",
        "Кузов"
    ]
}

async def seed_categories():
    engine = create_async_engine(DATABASE_URL)
    # Use expire_on_commit=False to prevent MissingGreenlet error on attribute access after commit
    async_session_factory = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_factory() as session:
        # Create tables if they don't exist
        async with engine.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)
            
        # NOTE: This is a destructive operation for categories to ensure structure match
        # In prod, handle more carefully. For now, we just add missing ones or update hierarchy.
        
        print("Seeding categories...")
        
        async def create_category(name, parent=None):
            slug = slugify(name)
            stmt = select(models.Category).where(models.Category.slug == slug)
            result = await session.execute(stmt)
            category = result.scalars().first()
            
            if not category:
                # To avoid lazy load error on print, we use the ID or just say "Parent"
                parent_name = parent.name if parent else 'None' 
                print(f"Creating: {name} (Parent: {parent_name})")
                
                category = models.Category(
                    name=name,
                    slug=slug,
                    parent_id=parent.id if parent else None
                )
                session.add(category)
                await session.commit()
                await session.refresh(category)
            else:
                # Update parent if needed (re-structuring)
                if category.parent_id != (parent.id if parent else None):
                    category.parent_id = parent.id if parent else None
                    session.add(category)
                    await session.commit()
            
            return category

        async def process_tree(tree, parent=None):
            if isinstance(tree, list):
                for item in tree:
                    if isinstance(item, str):
                        await create_category(item, parent)
                    elif isinstance(item, dict):
                        for key, val in item.items():
                            cat = await create_category(key, parent)
                            await process_tree(val, cat)
            elif isinstance(tree, dict):
                for key, val in tree.items():
                    cat = await create_category(key, parent)
                    await process_tree(val, cat)

        await process_tree(CATEGORIES_TREE)
        print("Categories seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_categories())

