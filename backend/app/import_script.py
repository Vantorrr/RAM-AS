import asyncio
import os
import openpyxl
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.future import select
from app import models, crud, schemas
from app.database import DATABASE_URL

# Helper to run async code
async def import_data(file_path: str):
    engine = create_async_engine(DATABASE_URL)
    async_session = AsyncSession(engine, expire_on_commit=False)

    print(f"Opening file: {file_path}")
    wb = openpyxl.load_workbook(file_path)
    sheet = wb.active

    async with async_session as session:
        # Create tables if not exist (for script usage)
        async with engine.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)

        print("Starting import...")
        # Skip header row
        for row in sheet.iter_rows(min_row=2, values_only=True):
            # Assumed Structure: 
            # Part Number | Name | Description | Price USD | Stock | Category
            part_number, name, description, price_usd, stock, category_name = row[0:6]
            
            if not part_number:
                continue

            # Handle Category
            category = None
            if category_name:
                stmt = select(models.Category).where(models.Category.name == category_name)
                result = await session.execute(stmt)
                category = result.scalars().first()
                if not category:
                    category = models.Category(name=category_name, slug=category_name.lower().replace(" ", "-"))
                    session.add(category)
                    await session.commit()
                    await session.refresh(category)
            
            # Check if product exists
            existing_product = await crud.get_product_by_part_number(session, str(part_number))
            
            if existing_product:
                print(f"Updating {part_number}...")
                existing_product.price_usd = price_usd
                existing_product.stock_quantity = stock
                existing_product.is_in_stock = stock > 0
                # Auto-calc ruble price (Mock rate 100)
                if price_usd:
                    existing_product.price_rub = float(price_usd) * 100 
            else:
                print(f"Creating {part_number}...")
                new_product = models.Product(
                    part_number=str(part_number),
                    name=name,
                    description=description,
                    price_usd=price_usd,
                    price_rub=float(price_usd) * 100 if price_usd else 0,
                    stock_quantity=stock,
                    is_in_stock=stock > 0,
                    category_id=category.id if category else None
                )
                session.add(new_product)
            
        await session.commit()
        print("Import completed!")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python import_script.py <path_to_excel>")
    else:
        asyncio.run(import_data(sys.argv[1]))








