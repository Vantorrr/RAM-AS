import asyncio
import sys
import os
import pandas as pd
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

# Add backend to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import models, crud, schemas
from app.database import DATABASE_URL

# Fallback DB URL if env var is missing (local dev)
if not DATABASE_URL:
    user = os.getenv("USER", "postgres")
    DATABASE_URL = f"postgresql+asyncpg://{user}:password@localhost:5432/ramus_db"

async def import_price_xls(file_path: str):
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    print(f"Reading Excel file: {file_path}...")
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    # Columns mapping based on inspection:
    # 'Наименование производителя' -> Brand
    # 'Номер детали' -> Part Number
    # 'Наименование' -> Name
    # 'Количество' -> Stock
    # 'Цена реализации Шт' -> Price Rub

    async with async_session() as session:
        # 1. Get or Create Default Category "Склад"
        default_cat_name = "Склад (New)"
        stmt = select(models.Category).where(models.Category.name == default_cat_name)
        result = await session.execute(stmt)
        default_category = result.scalars().first()

        if not default_category:
            print(f"Creating default category: {default_cat_name}")
            default_category = models.Category(
                name=default_cat_name,
                slug="sklad-new",
                parent_id=None
            )
            session.add(default_category)
            await session.commit()
            await session.refresh(default_category)
        
        print(f"Importing into category: {default_category.name} (ID: {default_category.id})")

        count_created = 0
        count_updated = 0
        
        # Iterate rows
        for index, row in df.iterrows():
            part_number = str(row['Номер детали']).strip()
            name = str(row['Наименование']).strip()
            manufacturer = str(row['Наименование производителя']).strip()
            
            # Parse Price
            try:
                price_rub = float(row['Цена реализации Шт'])
            except (ValueError, TypeError):
                price_rub = 0.0
            
            # Parse Stock
            try:
                stock = int(row['Количество'])
            except (ValueError, TypeError):
                stock = 0

            if not part_number or part_number.lower() == 'nan':
                continue

            # Construct full name if needed (Brand + Name)
            full_name = f"{manufacturer} {name}" if manufacturer and manufacturer.lower() != 'nan' else name

            # Check if exists
            existing_product = await crud.get_product_by_part_number(session, part_number)

            if existing_product:
                # Update
                existing_product.price_rub = price_rub
                existing_product.stock_quantity = stock
                existing_product.is_in_stock = stock > 0
                # Update name if it was empty or we want to override? Let's keep existing name if detailed, but update price/stock
                # actually let's update name too as this is the master file
                existing_product.name = full_name
                count_updated += 1
            else:
                # Create
                new_product = models.Product(
                    part_number=part_number,
                    name=full_name,
                    price_rub=price_rub,
                    # We don't have USD price, so we leave it None or calc. Let's leave None.
                    stock_quantity=stock,
                    is_in_stock=stock > 0,
                    category_id=default_category.id,
                    description=f"Производитель: {manufacturer}"
                )
                session.add(new_product)
                count_created += 1
            
            if index % 100 == 0:
                print(f"Processed {index} rows...")
                await session.commit() # Commit in batches

        await session.commit()
        print(f"Import Complete! Created: {count_created}, Updated: {count_updated}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file = sys.argv[1]
    else:
        file = "прайс.xls" # Default
    
    if os.path.exists(file):
        asyncio.run(import_price_xls(file))
    else:
        print(f"File not found: {file}")



