"""
БЫСТРАЯ ПРИВЯЗКА ТОВАРОВ К МАШИНАМ
Батчевая вставка - за 2-3 секунды!
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://postgres:CkxaAXQvcMFgovDSFMyYbiKTfdUYSxKN@maglev.proxy.rlwy.net:31084/railway"

engine = create_async_engine(DATABASE_URL)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def fast_link():
    print("🚀 БЫСТРАЯ ПРИВЯЗКА - СТАРТ!")
    print("=" * 60)
    
    async with async_session_maker() as session:
        # 1. ОЧИЩАЕМ
        print("🧹 Очистка...")
        await session.execute(text("TRUNCATE TABLE product_vehicles"))
        await session.commit()
        print("✅ Очищено!")
        
        # 2. ПОЛУЧАЕМ ТОВАРЫ
        result = await session.execute(text("SELECT id, name, part_number, manufacturer FROM products ORDER BY id"))
        products = result.fetchall()
        print(f"📦 Товаров: {len(products)}")
        
        # 3. ID ДИАПАЗОНЫ
        RAM_IDS = list(range(1, 47))
        DODGE_IDS = list(range(47, 140))
        JEEP_IDS = list(range(140, 186))
        CHRYSLER_IDS = list(range(186, 232))
        ALL_IDS = list(range(1, 232))
        
        UNIVERSAL = ['масло', 'oil', 'жидкость', 'fluid', 'моющ', 'wash', 'свеч', 'spark', 
                     'воздушн', 'air filter', 'салон', 'cabin', 'antifreeze', 'антифриз', 
                     'очистител', 'cleaner', 'присадк', 'additive', 'герметик', 'sealant',
                     'смазка', 'grease', 'brake fluid', 'тормозная жидкость']
        
        # 4. СОБИРАЕМ ВСЕ СВЯЗИ В ОДИН БАТЧ
        print("🔄 Анализ товаров...")
        all_inserts = []
        
        for pid, name, part_num, manuf in products:
            text_check = f"{name} {part_num or ''} {manuf or ''}".upper()
            
            # Определяем машины
            if any(kw.upper() in text_check for kw in UNIVERSAL):
                vehicle_ids = ALL_IDS
            elif 'RAM' in text_check or '1500' in text_check or '2500' in text_check:
                vehicle_ids = RAM_IDS
            elif 'DODGE' in text_check or 'CHALLENGER' in text_check or 'CHARGER' in text_check:
                vehicle_ids = DODGE_IDS
            elif 'JEEP' in text_check or 'WRANGLER' in text_check or 'CHEROKEE' in text_check:
                vehicle_ids = JEEP_IDS
            elif 'CHRYSLER' in text_check or 'PACIFICA' in text_check:
                vehicle_ids = CHRYSLER_IDS
            else:
                vehicle_ids = ALL_IDS
            
            # Добавляем в батч
            for vid in vehicle_ids:
                all_inserts.append(f"({pid},{vid})")
        
        print(f"✅ Подготовлено {len(all_inserts):,} связей")
        
        # 5. ОДНА МАССОВАЯ ВСТАВКА!
        print("💾 Вставка в БД...")
        batch_size = 5000
        for i in range(0, len(all_inserts), batch_size):
            batch = all_inserts[i:i+batch_size]
            values = ",".join(batch)
            
            await session.execute(text(f"""
                INSERT INTO product_vehicles (product_id, vehicle_id)
                VALUES {values}
                ON CONFLICT DO NOTHING
            """))
            
            if i % 50000 == 0:
                print(f"  → {i:,} / {len(all_inserts):,}")
        
        await session.commit()
        
        # 6. ПРОВЕРКА
        result = await session.execute(text("SELECT COUNT(*) FROM product_vehicles"))
        count = result.scalar()
        
        print("=" * 60)
        print(f"✅ ГОТОВО! Создано связей: {count:,}")
        print("🎯 Фильтрация по машинам теперь работает!")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fast_link())

