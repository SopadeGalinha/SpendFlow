from contextlib import asynccontextmanager
from fastapi import FastAPI  # type: ignore
from src.api.v1 import calendar


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup (Ex: cache connections, initialize resources, etc.)
    print("🚀 SpendFlow API is starting up...")
    yield
    # Shutdown (Ex: close connections, cleanup resources, etc.)
    print("🛑 SpendFlow API is shutting down...")


app = FastAPI(title="SpendFlow API v1", lifespan=lifespan)

# Routers
app.include_router(
    calendar.router,
    prefix="/api/v1/calendar",
    tags=["Calendar"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "version": "1.0.0",
        "message": "Welcome to SpendFlow! Visit /docs for API documentation.",
    }
