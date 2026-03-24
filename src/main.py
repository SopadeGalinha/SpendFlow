import logging.config
from fastapi import FastAPI, Depends, HTTPException
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.logging_config import LOGGING_CONFIG
from src.core.exceptions import (
    global_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from src.core.middleware import RateLimitMiddleware, SecurityHeadersMiddleware
from src.core.lifespan import lifespan
from src.core.cors import add_cors_middleware
from src.api.router import include_routers
from src.database import get_session

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

app = FastAPI(title="SpendFlow API v1", lifespan=lifespan)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
add_cors_middleware(app)
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
include_routers(app)


@app.get("/health")
async def health_check(session: AsyncSession = Depends(get_session)):
    try:
        await session.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger = logging.getLogger("src.main")
        logger.error("Health check failed", extra={"error": str(e)})
        raise HTTPException(status_code=503, detail="Database unavailable")


@app.get("/")
async def root():
    return {"status": "online", "version": "1.0.0"}
