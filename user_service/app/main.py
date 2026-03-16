"""User Service – Kullanıcı profilleri ve favori maç takibi."""

from fastapi import FastAPI

app = FastAPI(
    title="User Service",
    description="Kullanıcı profilleri ve favori maç takibi yönetimi servisi.",
    version="0.1.0",
)


@app.get("/health", tags=["health"])
async def health_check():
    """User Service sağlık kontrolü."""
    return {"status": "ok", "service": "user-service"}
