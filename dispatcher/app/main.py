"""
Dispatcher – FastAPI Uygulama Giriş Noktası (OOP / SOLID Uyumlu)

Sorumluluklar:
    - FastAPI uygulamasını oluşturmak
    - Dependency Injection ile RouterService'i endpoint'lere sağlamak
    - HTTP yanıtlarını standart formata dönüştürmek

Not: Bu dosya yalnızca "giriş noktası" (composition root) görevi görür.
     İş mantığı tamamen `RouterService` sınıfındadır.
"""

from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse, Response
import httpx

from app.services.router import (
    BaseRouterService,
    RouterService,
    ServiceRegistry,
)
from app.middleware.auth import AuthMiddleware, HttpTokenVerifier
from app.middleware.error_handler import ErrorHandlerMiddleware, ErrorHandler, AppLogger

app = FastAPI(
    title="Dispatcher API Gateway",
    description="Canlı Skor & Bahis Oranları Sistemi Dispatcher",
)

# 1. Error Handler Middleware (En diştaki katman olmalı, tüm hataları yakalamak için)
logger = AppLogger()
error_handler = ErrorHandler(logger=logger)
app.add_middleware(ErrorHandlerMiddleware, error_handler=error_handler)

# 2. Auth Middleware (Hata yakalayıcının altında çalışır)
token_verifier = HttpTokenVerifier()
app.add_middleware(AuthMiddleware, token_verifier=token_verifier)

def get_router_service() -> BaseRouterService:
    """
    FastAPI Depends() mekanizması ile endpoint'lere enjekte edilen
    RouterService fabrika fonksiyonu.

    Döndürülen tür `BaseRouterService` (soyut arayüz) olduğundan,
    Dependency Inversion Principle (DIP) sağlanmaktadır.
    """
    registry = ServiceRegistry()
    return RouterService(registry=registry)


# ---------------------------------------------------------------------------
# Endpoint'ler
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    """Dispatcher sağlık kontrolü endpoint'i."""
    return {"status": "ok", "service": "dispatcher"}


@app.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
)
async def route_request(
    request: Request,
    path: str,
    router: BaseRouterService = Depends(get_router_service),
):
    """
    Gelen tüm istekleri URL path'ine göre ilgili mikroservise yönlendirir.

    URL çözümleme ve yönlendirme mantığı tamamen `RouterService` sınıfına
    devredilmiştir (Single Responsibility Principle).
    """
    # Hedef URL'yi belirle 
    target_url = router.resolve_target_url(path)

    if target_url is None:
        return JSONResponse(
            status_code=404,
            content={"detail": "Route not mapped to any service"},
        )

    # İsteği hedef servise ilet
    resp = await router.forward_request(target_url, request)

    if resp is None:
        return JSONResponse(
            status_code=502,
            content={"detail": "Bad Gateway – Service unavailable"},
        )

    # httpx yanıtını FastAPI yanıtına dönüştür
    if isinstance(resp, httpx.Response):
        if resp.status_code == 204:
            return Response(status_code=204)
        try:
            return JSONResponse(status_code=resp.status_code, content=resp.json())
        except Exception:
            return Response(status_code=resp.status_code, content=resp.content)

    return resp
