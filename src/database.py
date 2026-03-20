from sqlalchemy.orm import sessionmaker  # type: ignore
from sqlalchemy.ext.asyncio import (  # type: ignore
    create_async_engine,
    AsyncSession,
)
from src.core.config import settings


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    future=True,
)


async def get_session() -> AsyncSession:
    """Provides an asynchronous database session for FastAPI routes."""
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session() as session:
        yield session
