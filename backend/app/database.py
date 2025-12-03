from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Get DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Railway gives postgres:// but SQLAlchemy needs postgresql+asyncpg://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    # Local development fallback
    user = os.getenv("USER", "postgres")
    DATABASE_URL = f"postgresql+asyncpg://{user}:password@localhost:5432/ramus_db"

engine = create_async_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

Base = declarative_base()

async def get_db():
    async with SessionLocal() as session:
        yield session
