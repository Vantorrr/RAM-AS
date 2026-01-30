"""
Добавляет колонку is_preorder в таблицу order_items
"""
import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)

print("🔧 Добавляю колонку is_preorder в order_items...")

with engine.connect() as conn:
    try:
        # Добавляем колонку
        conn.execute(text("""
            ALTER TABLE order_items 
            ADD COLUMN IF NOT EXISTS is_preorder BOOLEAN DEFAULT FALSE
        """))
        conn.commit()
        print("✅ Колонка is_preorder успешно добавлена!")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

print("✅ Миграция завершена!")
