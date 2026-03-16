"""Auth Service – Kullanıcı kimlik doğrulama ve JWT yönetimi."""

from fastapi import FastAPI

app = FastAPI(
    title="Auth Service",
    description="Kullanıcı kaydı, girişi ve JWT token yönetimi servisi.",
    version="0.1.0",
)


@app.get("/health", tags=["health"])
async def health_check():
    """Auth Service sağlık kontrolü."""
    return {"status": "ok", "service": "auth-service"}
