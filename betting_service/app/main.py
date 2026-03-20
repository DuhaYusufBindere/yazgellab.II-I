"""Betting Service – Canlı bahis oranları yönetimi."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routes.odds import router as odds_router
from app.services.redis_client import RedisClient


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Uygulama yaşam döngüsü: kapanışta Redis bağlantısını temizler."""
    yield
    await RedisClient.close()


app = FastAPI(
    title="Betting Service",
    description="Maç skorlarına göre değişen canlı bahis oranlarının takibi servisi.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(odds_router)


@app.get("/health", tags=["health"])
async def health_check():
    """Betting Service sağlık kontrolü."""
    return {"status": "ok", "service": "betting-service"}
