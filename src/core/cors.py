import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings


def add_cors_middleware(app: FastAPI) -> None:
    """Configure and add CORS middleware to the FastAPI application."""
    # In production, CORS_ORIGINS must be explicitly set.
    # Default to an empty list for safety.
    cors_origins = (
        settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS else []
    )

    # In debug, provide sensible defaults for local dev frontends if not set.
    if settings.DEBUG and not cors_origins:
        cors_origins = [
            "http://localhost:3000",  # Next.js dev
            "http://localhost:4200",  # Angular dev
        ]
    if not cors_origins and not settings.DEBUG:
        logger = logging.getLogger(__name__)
        logger.warning(
            "CORS_ORIGINS not configured. "
            "No origins will be allowed in production."
        )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


__all__ = ["add_cors_middleware"]
