import logging
from contextlib import asynccontextmanager

from src.database import AsyncSessionLocal
from src.services import CategoryService


@asynccontextmanager
async def lifespan(app):
    logger = logging.getLogger("src.main")
    logger.info("🚀 SpendFlow API is starting up...")
    async with AsyncSessionLocal() as session:
        await CategoryService.bootstrap_system_catalog(session)
    yield
    logger.info("🛑 SpendFlow API is shutting down...")


__all__ = ["lifespan"]
