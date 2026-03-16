"""Match Service – Canlı maç skoru yönetimi."""

from fastapi import FastAPI

app = FastAPI(
    title="Match Service",
    description="Canlı maç skorlarının yönetimi ve dağıtımı servisi.",
    version="0.1.0",
)


@app.get("/health", tags=["health"])
async def health_check():
    """Match Service sağlık kontrolü."""
    return {"status": "ok", "service": "match-service"}
