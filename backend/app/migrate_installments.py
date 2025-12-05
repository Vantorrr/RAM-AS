import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text

# Migration script to add column to existing DB without dropping it
async def migrate_db():
    user = os.getenv("USER", "postgres")
    # Ensure this matches your actual running DB connection
    DATABASE_URL = os.getenv("DATABASE_URL", f"postgresql+asyncpg://{user}:password@localhost:5432/ramus_db")
    
    engine = create_async_engine(DATABASE_URL)
    
    async with engine.begin() as conn:
        try:
            print("Attempting to add is_installment_available column...")
            await conn.execute(text("ALTER TABLE products ADD COLUMN is_installment_available BOOLEAN DEFAULT FALSE"))
            print("Migration successful!")
        except Exception as e:
            print(f"Migration skipped or failed (Column likely exists): {e}")

if __name__ == "__main__":
    asyncio.run(migrate_db())





