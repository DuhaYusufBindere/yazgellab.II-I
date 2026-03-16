"""Dispatcher (API Gateway) – Sistemin tek giriş noktası."""

from fastapi import FastAPI

app = FastAPI(
    title="Dispatcher – API Gateway",
    description="Canlı Skor & Bahis Oranları sistemi için merkezi yönlendirme ve yetkilendirme gateway'i.",
    version="0.1.0",
)


@app.get("/health", tags=["health"])
async def health_check():
    """Dispatcher sağlık kontrolü."""
    return {"status": "ok", "service": "dispatcher"}
