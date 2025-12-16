import asyncio
import os
import pandas as pd
from sqlalchemy import select
from app.database import SessionLocal
from app import models

# Путь к файлу (от корня проекта)
FILE_PATH = "Прайс_мск-4.xls"

async def import_data():
    print(f"📂 Читаем файл {FILE_PATH}...")
    
    try:
        df = pd.read_excel(FILE_PATH, header=None)
    except FileNotFoundError:
        print("❌ Файл не найден! Проверьте, что он лежит в корне проекта.")
        return

    print(f"✅ Файл прочитан. Строк: {len(df)}")
    
    async with SessionLocal() as db:
        # 1. Находим категорию "Мультибренд"
        category_name = "Мультибренд"
        result = await db.execute(select(models.Category).where(models.Category.name == category_name))
        category = result.scalars().first()
        
        if not category:
            print(f"⚠️ Категория '{category_name}' не найдена. Создаем...")
            category = models.Category(name=category_name, image_url=None)
            db.add(category)
            await db.commit()
            await db.refresh(category)
        
        print(f"✅ Используем категорию: {category.name} (ID {category.id})")

        # 2. Импорт / Обновление
        count_new = 0
        count_updated = 0
        
        print("🚀 Начинаем обработку...")
        
        # Получаем карту существующих товаров: part_number -> Product
        # Чтобы не делать запрос на каждый row
        print("🔄 Загружаем базу товаров...")
        existing_products_query = await db.execute(select(models.Product))
        existing_products_list = existing_products_query.scalars().all()
        # Создаем словарь для быстрого поиска
        existing_map = {p.part_number: p for p in existing_products_list}
        
        for index, row in df.iterrows():
            brand = str(row[0]).strip()
            part_number = str(row[1]).strip()
            name = str(row[2]).strip()
            try:
                quantity = int(row[3])
            except:
                quantity = 0
            
            try:
                price = float(row[5])
            except:
                price = 0.0

            if price <= 0 or not part_number or part_number == 'nan':
                continue

            product = existing_map.get(part_number)

            if product:
                # ОБНОВЛЯЕМ существующий и ПЕРЕНОСИМ в Мультибренд
                if product.category_id != category.id:
                    product.category_id = category.id # Переносим!
                
                product.stock_quantity = quantity
                product.price_rub = price
                product.is_in_stock = True # Всегда в наличии
                
                count_updated += 1
            else:
                # СОЗДАЕМ новый
                new_product = models.Product(
                    name=name,
                    part_number=part_number,
                    description=f"Производитель: {brand}",
                    price_rub=price,
                    stock_quantity=quantity,
                    is_in_stock=True,
                    category_id=category.id, # Мультибренд
                    manufacturer=brand,
                    image_url=None,
                    seller_id=None
                )
                db.add(new_product)
                existing_map[part_number] = new_product # Добавляем в мапу
                count_new += 1
            
            if (index + 1) % 500 == 0:
                await db.commit()
                print(f"   Обработано {index + 1} строк... (New: {count_new}, Upd: {count_updated})")

        await db.commit()
        print(f"🎉 Готово!")
        print(f"   Перенесено/Обновлено: {count_updated}")
        print(f"   Добавлено новых: {count_new}")

if __name__ == "__main__":
    asyncio.run(import_data())
