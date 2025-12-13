from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine
import os

# Get DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Railway gives postgres:// but SQLAlchemy needs postgresql+asyncpg://
    if DATABASE_URL.startswith("postgres://"):
        ASYNC_DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
        # Sync URL для sqladmin (psycopg2)
        SYNC_DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
        SYNC_DATABASE_URL = DATABASE_URL
    else:
        ASYNC_DATABASE_URL = DATABASE_URL
        SYNC_DATABASE_URL = DATABASE_URL.replace("+asyncpg", "")
else:
    # Local development fallback
    user = os.getenv("USER", "postgres")
    ASYNC_DATABASE_URL = f"postgresql+asyncpg://{user}:password@localhost:5432/ramus_db"
    SYNC_DATABASE_URL = f"postgresql://{user}:password@localhost:5432/ramus_db"

# Async engine (для FastAPI endpoints)
engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)

SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

# Sync engine (для sqladmin)
sync_engine = create_engine(SYNC_DATABASE_URL, echo=False)

Base = declarative_base()

async def get_db():
    async with SessionLocal() as session:
        yield session
