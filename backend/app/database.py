from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Fallback to current user if postgres role fails in dev
user = os.getenv("USER", "postgres")
DATABASE_URL = os.getenv("DATABASE_URL", f"postgresql+asyncpg://{user}:password@localhost:5432/ramus_db")

# If the above default connection string fails, you might need to adjust it manually 
# to match your local postgres setup (e.g., remove password if ident auth is used).

engine = create_async_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

Base = declarative_base()

async def get_db():
    async with SessionLocal() as session:
        yield session
