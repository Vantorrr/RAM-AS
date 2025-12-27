"""
🤖 AI-ПРИВЯЗКА ТОВАРОВ К АВТОМОБИЛЯМ
Скрипт анализирует все товары и привязывает их к подходящим машинам
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from dotenv import load_dotenv
import openai

# Загружаем .env
load_dotenv()

# Подключение к БД
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise Exception("DATABASE_URL не найден!")

# Исправляем postgres:// на postgresql+asyncpg://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

# OpenAI API (используем OpenRouter)
openai.api_key = "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"
openai.base_url = "https://openrouter.ai/api/v1"

# Создаём async движок
engine = create_async_engine(DATABASE_URL)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_all_products():
    """Получить все продукты"""
    async with async_session_maker() as session:
        result = await session.execute(text("""
            SELECT id, name, part_number, manufacturer 
            FROM products 
            ORDER BY id
        """))
        return [
            {
                "id": row[0],
                "name": row[1],
                "part_number": row[2],
                "manufacturer": row[3]
            }
            for row in result
        ]

async def get_all_vehicles():
    """Получить все машины"""
    async with async_session_maker() as session:
        result = await session.execute(text("""
            SELECT id, make, model, generation, year_from, year_to, engine
            FROM vehicles
            ORDER BY id
        """))
        return [
            {
                "id": row[0],
                "make": row[1],
                "model": row[2],
                "generation": row[3],
                "year_from": row[4],
                "year_to": row[5],
                "engine": row[6]
            }
            for row in result
        ]

def analyze_product_with_ai(product, vehicles):
    """
    Анализирует продукт через GPT-4o-mini и возвращает список ID подходящих машин
    """
    vehicles_text = "\n".join([
        f"{v['id']}: {v['make']} {v['model']} {v['generation'] or ''} ({v['year_from']}-{v['year_to'] or 'наст.вр.'}) {v['engine'] or ''}".strip()
        for v in vehicles
    ])
    
    prompt = f"""Ты эксперт по автозапчастям для американских машин (RAM, Dodge, Jeep, Chrysler).

ТОВАР:
Название: {product['name']}
Артикул: {product['part_number']}
Производитель: {product['manufacturer'] or 'не указан'}

СПИСОК АВТОМОБИЛЕЙ:
{vehicles_text}

ЗАДАЧА: 
Определи, к каким автомобилям подходит эта деталь. Вернуть ТОЛЬКО ID автомобилей через запятую.

ПРАВИЛА:
1. Если деталь УНИВЕРСАЛЬНАЯ (масло, жидкости, свечи, фильтры воздуха/салона) → ВСЕ ID
2. Если деталь для КОНКРЕТНОЙ модели/двигателя → только подходящие ID
3. Если деталь для RAM → все RAM (ID: 1-46)
4. Если деталь для Dodge → все Dodge (ID: 47-139)
5. Если деталь для Jeep → все Jeep (ID: 140-185)
6. Если деталь для Chrysler → все Chrysler (ID: 186-231)

ФОРМАТ ОТВЕТА: только ID через запятую (например: 1,2,3,5,8)
Если непонятно → верни все ID от 1 до 231.
"""

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты эксперт по автозапчастям. Отвечаешь ТОЛЬКО списком ID."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        answer = response.choices[0].message.content.strip()
        
        # Парсим ID
        vehicle_ids = []
        for part in answer.split(','):
            try:
                vid = int(part.strip())
                if 1 <= vid <= 231:
                    vehicle_ids.append(vid)
            except:
                continue
        
        # Если ничего не распарсилось - универсальная деталь
        if not vehicle_ids:
            vehicle_ids = list(range(1, 232))
        
        return vehicle_ids
        
    except Exception as e:
        print(f"❌ Ошибка AI для товара {product['id']}: {e}")
        # При ошибке считаем универсальной
        return list(range(1, 232))

async def save_links(product_id, vehicle_ids):
    """Сохранить связи в БД"""
    async with async_session_maker() as session:
        for vid in vehicle_ids:
            try:
                await session.execute(text("""
                    INSERT INTO product_vehicles (product_id, vehicle_id)
                    VALUES (:pid, :vid)
                    ON CONFLICT DO NOTHING
                """), {"pid": product_id, "vid": vid})
            except:
                pass
        await session.commit()

async def main():
    print("🚀 ЗАПУСК AI-ПРИВЯЗКИ ТОВАРОВ К АВТОМОБИЛЯМ")
    print("=" * 60)
    
    # Очищаем таблицу
    print("🧹 Очистка старых связей...")
    async with async_session_maker() as session:
        await session.execute(text("TRUNCATE TABLE product_vehicles"))
        await session.commit()
    print("✅ Таблица очищена!")
    
    # Получаем данные
    print("📦 Загрузка товаров...")
    products = await get_all_products()
    print(f"✅ Загружено {len(products)} товаров")
    
    print("🚗 Загрузка автомобилей...")
    vehicles = await get_all_vehicles()
    print(f"✅ Загружено {len(vehicles)} автомобилей")
    
    # Обрабатываем
    print("🤖 Начинаем анализ через GPT-4o-mini...")
    print("=" * 60)
    
    total = len(products)
    processed = 0
    
    for product in products:
        processed += 1
        
        # Анализируем
        vehicle_ids = analyze_product_with_ai(product, vehicles)
        
        # Сохраняем
        await save_links(product['id'], vehicle_ids)
        
        # Прогресс
        percent = (processed / total) * 100
        print(f"[{processed}/{total}] ({percent:.1f}%) | Товар #{product['id']} → {len(vehicle_ids)} машин")
        
        # Задержка, чтобы не превысить rate limit OpenAI
        if processed % 10 == 0:
            await asyncio.sleep(1)  # 1 секунда каждые 10 товаров
    
    print("=" * 60)
    print("✅ ГОТОВО! Все товары привязаны к автомобилям!")
    
    # Статистика
    async with async_session_maker() as session:
        result = await session.execute(text("SELECT COUNT(*) FROM product_vehicles"))
        links_count = result.scalar()
        print(f"📊 Создано связей: {links_count:,}")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
