from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from src.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Provides an asynchronous database session for FastAPI routes."""
    async with AsyncSessionLocal() as session:
        yield session
