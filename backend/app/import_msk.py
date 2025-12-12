import asyncio
import pandas as pd
from sqlalchemy import select
from app.database import SessionLocal
from app.models import Product, Category

# Путь к файлу
FILE_PATH = "../Прайс_мск-4.xls"

async def import_msk():
    print(f"🚀 Начинаю импорт из {FILE_PATH}...")
    
    # Читаем Excel без заголовка (header=None)
    try:
        df = pd.read_excel(FILE_PATH, header=None)
    except Exception as e:
        print(f"❌ Ошибка чтения файла: {e}")
        return

    async with SessionLocal() as session:
        # 1. Получаем категорию "Склад" или создаем "Склад (Москва)"
        # Проверим, есть ли категория "Склад", иначе создадим
        result = await session.execute(select(Category).where(Category.name.ilike("%Склад%")))
        default_category = result.scalars().first()
        
        if not default_category:
            print("⚠️ Категория 'Склад' не найдена. Создаю 'Склад (New)'...")
            default_category = Category(name="Склад (New)", slug="warehouse-new", image_url=None)
            session.add(default_category)
            await session.commit()
            await session.refresh(default_category)
        
        print(f"📂 Категория по умолчанию: {default_category.name} (ID: {default_category.id})")

        # Кэш существующих товаров для быстрого поиска (part_number -> Product)
        print("📥 Загружаю текущую базу товаров...")
        existing_products_query = await session.execute(select(Product))
        existing_products = {p.part_number: p for p in existing_products_query.scalars().all()}
        
        new_count = 0
        updated_count = 0
        
        # 2. Проходим по строкам
        for index, row in df.iterrows():
            manufacturer = str(row[0]).strip() if pd.notna(row[0]) else "Unknown"
            part_number = str(row[1]).strip()
            name = str(row[2]).strip()
            qty = int(row[3]) if pd.notna(row[3]) else 0
            # Цена продажи в колонке 5 (index 5)
            price = float(row[5]) if pd.notna(row[5]) else 0.0

            if not part_number or part_number == "nan":
                continue

            # Логика обновления / создания
            if part_number in existing_products:
                # Товар есть -> ОБНОВЛЯЕМ (суммируем остатки)
                product = existing_products[part_number]
                old_qty = product.stock_quantity
                product.stock_quantity += qty
                # Обновляем цену (берем новую, если она > 0)
                if price > 0:
                    product.price_rub = price
                
                # Если товар был "Нет в наличии", а теперь появился
                if product.stock_quantity > 0:
                    product.is_in_stock = True
                    
                updated_count += 1
                # print(f"Updated {part_number}: Qty {old_qty} -> {product.stock_quantity}")
            else:
                # Товара нет -> СОЗДАЕМ
                new_product = Product(
                    name=name,
                    part_number=part_number,
                    manufacturer=manufacturer,
                    description=f"Производитель: {manufacturer}",
                    price_rub=price,
                    stock_quantity=qty,
                    is_in_stock=(qty > 0),
                    category_id=default_category.id, # Пока кидаем в Склад, потом распределим
                    image_url=None # Фото нет
                )
                session.add(new_product)
                # Добавляем в кэш, чтобы не дублировать внутри файла (если вдруг дубли в файле)
                existing_products[part_number] = new_product
                new_count += 1
            
            if index % 1000 == 0:
                print(f"Processed {index} rows...")

        await session.commit()
        print(f"✅ Импорт завершен!")
        print(f"🆕 Новых товаров: {new_count}")
        print(f"🔄 Обновленных товаров: {updated_count}")

if __name__ == "__main__":
    asyncio.run(import_msk())

