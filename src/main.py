from fastapi import FastAPI
from src.database import init_db
from src.api.v1 import calendar # Importamos o novo router

app = FastAPI(title="SpendFlow API v1")

@app.on_event("startup")
async def on_startup():
    await init_db()

# Registro das rotas
app.include_router(calendar.router, prefix="/api/v1/calendar", tags=["Calendar"])

@app.get("/")
async def root():
    return {"status": "SpendFlow Online"}