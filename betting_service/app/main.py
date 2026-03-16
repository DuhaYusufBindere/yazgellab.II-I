"""Betting Service – Canlı bahis oranları yönetimi."""

from fastapi import FastAPI

app = FastAPI(
    title="Betting Service",
    description="Maç skorlarına göre değişen canlı bahis oranlarının takibi servisi.",
    version="0.1.0",
)


@app.get("/health", tags=["health"])
async def health_check():
    """Betting Service sağlık kontrolü."""
    return {"status": "ok", "service": "betting-service"}
