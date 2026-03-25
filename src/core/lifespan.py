import logging
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app):
    logger = logging.getLogger("src.main")
    logger.info("🚀 SpendFlow API is starting up...")
    yield
    logger.info("🛑 SpendFlow API is shutting down...")


__all__ = ["lifespan"]
