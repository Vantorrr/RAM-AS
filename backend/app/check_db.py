import asyncio
from sqlalchemy import select, func
from app.database import SessionLocal
from app.models import Product

async def check_products():
    async with SessionLocal() as db:
        result = await db.execute(select(func.count(Product.id)))
        count = result.scalar()
        print(f"Товаров в БД: {count}")
        
        # Первые 5 товаров
        result = await db.execute(select(Product).limit(5))
        products = result.scalars().all()
        print("\nПервые 5 товаров:")
        for p in products:
            print(f"- {p.id}: {p.name} ({p.part_number}) - {p.price_rub} ₽")

if __name__ == "__main__":
    asyncio.run(check_products())






