from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import DatabaseManager
from app.routes.matches import router as matches_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    DatabaseManager.connect_to_database()
    yield
    DatabaseManager.close_database_connection()

app = FastAPI(
    title="Match Service",
    description="Canlı skor ve maç verilerini yöneten RMM uyumlu mikroservis.",
    lifespan=lifespan
)

app.include_router(matches_router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "match-service"}
