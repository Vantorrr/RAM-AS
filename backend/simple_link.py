"""
ПРОСТАЯ ПРИВЯЗКА ТОВАРОВ К МАШИНАМ
Без AI, просто по ключевым словам в названии
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise Exception("DATABASE_URL не найден!")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DATABASE_URL)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def link_products():
    print("🚀 НАЧАЛО ПРИВЯЗКИ ТОВАРОВ")
    print("=" * 60)
    
    async with async_session_maker() as session:
        # Очищаем таблицу
        print("🧹 Очистка product_vehicles...")
        await session.execute(text("TRUNCATE TABLE product_vehicles"))
        await session.commit()
        print("✅ Очищено!")
        
        # Получаем товары
        result = await session.execute(text("""
            SELECT id, name, part_number, manufacturer 
            FROM products 
            ORDER BY id
        """))
        products = result.fetchall()
        print(f"📦 Загружено {len(products)} товаров")
        
        # ID диапазоны машин
        RAM_IDS = list(range(1, 47))        # 1-46
        DODGE_IDS = list(range(47, 140))    # 47-139
        JEEP_IDS = list(range(140, 186))    # 140-185
        CHRYSLER_IDS = list(range(186, 232))# 186-231
        ALL_IDS = list(range(1, 232))       # 1-231
        
        # Универсальные детали
        UNIVERSAL_KEYWORDS = [
            'масло', 'oil', 'жидкость', 'fluid', 'моющ', 'wash',
            'свеч', 'spark', 'воздушн', 'air filter', 'салон', 'cabin',
            'antifreeze', 'антифриз', 'очистител', 'cleaner',
            'присадк', 'additive', 'герметик', 'sealant',
            'смазка', 'grease', 'brake fluid', 'тормозная жидкость'
        ]
        
        total_links = 0
        
        for idx, (product_id, name, part_number, manufacturer) in enumerate(products, 1):
            # Объединяем название + артикул + производитель для анализа
            text_to_check = f"{name} {part_number or ''} {manufacturer or ''}".upper()
            
            vehicle_ids = []
            reason = ""
            
            # 1. Проверяем универсальные детали
            is_universal = any(kw.upper() in text_to_check for kw in UNIVERSAL_KEYWORDS)
            
            if is_universal:
                vehicle_ids = ALL_IDS
                reason = "УНИВЕРСАЛЬНАЯ"
            # 2. Проверяем конкретные марки
            elif 'RAM' in text_to_check or '1500' in text_to_check or '2500' in text_to_check:
                vehicle_ids = RAM_IDS
                reason = "RAM"
            elif 'DODGE' in text_to_check or 'CHALLENGER' in text_to_check or 'CHARGER' in text_to_check or 'DURANGO' in text_to_check:
                vehicle_ids = DODGE_IDS
                reason = "DODGE"
            elif 'JEEP' in text_to_check or 'WRANGLER' in text_to_check or 'CHEROKEE' in text_to_check or 'GRAND CHEROKEE' in text_to_check:
                vehicle_ids = JEEP_IDS
                reason = "JEEP"
            elif 'CHRYSLER' in text_to_check or 'PACIFICA' in text_to_check or '300' in text_to_check:
                vehicle_ids = CHRYSLER_IDS
                reason = "CHRYSLER"
            # 3. Если непонятно - ко всем
            else:
                vehicle_ids = ALL_IDS
                reason = "ВСЕ (default)"
            
            # Вставляем связи батчем
            for vid in vehicle_ids:
                await session.execute(text("""
                    INSERT INTO product_vehicles (product_id, vehicle_id)
                    VALUES (:pid, :vid)
                    ON CONFLICT DO NOTHING
                """), {"pid": product_id, "vid": vid})
            
            total_links += len(vehicle_ids)
            
            # Прогресс
            if idx % 100 == 0:
                await session.commit()
                percent = (idx / len(products)) * 100
                print(f"[{idx}/{len(products)}] ({percent:.1f}%) | Создано связей: {total_links:,}")
            
            # Примеры
            if idx <= 5:
                print(f"  → Товар #{product_id}: {name[:50]} → {reason} ({len(vehicle_ids)} машин)")
        
        # Финальный коммит
        await session.commit()
        
        print("=" * 60)
        print("✅ ГОТОВО!")
        print(f"📊 Всего связей: {total_links:,}")
        
        # Проверка
        result = await session.execute(text("SELECT COUNT(*) FROM product_vehicles"))
        db_count = result.scalar()
        print(f"✅ В БД: {db_count:,}")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(link_products())

