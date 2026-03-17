"""Auth Service – Kullanıcı kimlik doğrulama ve JWT yönetimi."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routes.auth import router as auth_router
from app.services.redis_client import RedisClient


@asynccontextmanager
async def lifespan(application: FastAPI):
    yield
    await RedisClient.close()


app = FastAPI(
    title="Auth Service",
    description="Kullanıcı kaydı, girişi ve JWT token yönetimi servisi.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(auth_router)


@app.get("/health", tags=["health"])
async def health_check():
    """Auth Service sağlık kontrolü."""
    return {"status": "ok", "service": "auth-service"}
