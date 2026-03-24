
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings


def add_cors_middleware(app):
    cors_origins = (
        settings.CORS_ORIGINS.split(",")
        if settings.CORS_ORIGINS else ["*"]
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


__all__ = ["add_cors_middleware"]
