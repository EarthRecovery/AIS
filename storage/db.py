import os
from functools import lru_cache
from typing import AsyncIterator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

# Load environment variables early so DATABASE_URL is available.
load_dotenv()

Base = declarative_base()


@lru_cache
def get_db_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    return url


# Create async engine/session factory.
engine = create_async_engine(get_db_url(), echo=False, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that yields an async DB session."""
    async with SessionLocal() as session:
        yield session
