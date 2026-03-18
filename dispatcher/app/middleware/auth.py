from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import httpx

class AuthMiddleware(BaseHTTPMiddleware):
    """
    Dispatcher servisi için JWT yetkilendirme katmanıdır.
    Gelen isteklerin Authorization header'ını kontrol eder ve
    geçerli olup olmadığını Auth Service'e sorar.
    """
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # Token kontrolünden muaf tutulacak public endpointler
        if path.startswith("/auth/") or path == "/health" or path == "/":
            return await call_next(request)
            
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401, 
                content={"detail": "Missing Authorization header"}
            )
            
        token = auth_header.split(" ")[1]
        
        # Token'ı doğrulamak için Auth Service'e istek atılır
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://auth-service:8001/auth/verify",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
            if response.status_code != 200:
                # Gelen hata mesajını (ör. Token expired veya Invalid token) aynen geri dön
                try:
                    error_detail = response.json().get("detail", "Unauthorized")
                except Exception:
                    error_detail = "Unauthorized"
                return JSONResponse(status_code=401, content={"detail": error_detail})
                
        except Exception as e:
            return JSONResponse(
                status_code=502, 
                content={"detail": f"Auth service unavailable: {str(e)}"}
            )
            
        # İstek başarılıysa router'a ve hedef servise gitmesine izin ver
        return await call_next(request)
