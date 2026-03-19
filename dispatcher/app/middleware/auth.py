from abc import ABC, abstractmethod
from typing import Optional
import httpx
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

class BaseTokenVerifier(ABC):
    """Token doğrulama işlemleri için soyut arayüz (DIP + ISP)."""
    @abstractmethod
    async def verify_token(self, token: str) -> bool:
        pass

class HttpTokenVerifier(BaseTokenVerifier):
    """Auth Service'e HTTP isteğiatarak token'ı doğrulayan somut sınıf (SRP)."""
    def __init__(self, auth_service_url: str = "http://auth-service:8001/auth/verify"):
        self.auth_service_url = auth_service_url

    async def verify_token(self, token: str) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.auth_service_url,
                    headers={"Authorization": f"Bearer {token}"}
                )
            if response.status_code != 200:
                try:
                    error_detail = response.json().get("detail", "Unauthorized")
                except Exception:
                    error_detail = "Unauthorized"
                raise ValueError(error_detail)
            return True
        except ValueError as e:
            # Token doğrulama reddedildi (İstemci hatası - 401 için)
            raise e
        except Exception as e:
            # Servise erişilemedi veya altyapı sıkıntısı (Sunucu hatası - 502 için)
            raise RuntimeError(str(e))

class AuthMiddleware(BaseHTTPMiddleware):
    """
    Dispatcher servisi için JWT yetkilendirme katmanı.
    SOLID prensiplerine uygun şekilde parçalanarak refactor edilmiştir.
    """
    def __init__(self, app, token_verifier: 'BaseTokenVerifier'):
        super().__init__(app)
        # Sıkı DIP (Bağımlılığı Tersine Çevirme):
        # Middleware ASLA somut bir sınıfa bağımlı değildir. 
        # Kesinlikle dışarıdan (main.py'den) soyut sınıf Interface'ini (BaseTokenVerifier) devralır.
        self.token_verifier = token_verifier
        
        # OCP: Bu listeler dışarıdan config olarak da alınabilir.
        self.public_paths = {"/health", "/", "/metrics"}
        self.public_prefixes = ("/auth/",)

    def _is_public_route(self, path: str) -> bool:
        """SRP: Rotanın public olup olmadığını denetler."""
        if path in self.public_paths:
            return True
        if path.startswith(self.public_prefixes):
            return True
        return False

    def _extract_token(self, auth_header: Optional[str]) -> str:
        """SRP: Header formunu denetler ve salt token'ı çıkarır."""
        if not auth_header or not auth_header.startswith("Bearer "):
            raise ValueError("Missing Authorization header")
        return auth_header.split(" ")[1]

    async def dispatch(self, request: Request, call_next):
        """SRP: Sadece HTTP istek akışını ve hata yönetimini koordine eder."""
        if self._is_public_route(request.url.path):
            return await call_next(request)

        try:
            token = self._extract_token(request.headers.get("Authorization"))
            await self.token_verifier.verify_token(token)
        except ValueError as e:
            return JSONResponse(status_code=401, content={"detail": str(e)})
        except RuntimeError as e:
            return JSONResponse(status_code=502, content={"detail": f"Auth service unavailable: {str(e)}"})

        return await call_next(request)
