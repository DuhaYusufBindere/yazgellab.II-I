import time
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from fastapi import Request

class BaseRateLimiter:
    """Base abstract class for rate limiters (OOP)."""
    def is_allowed(self, client_id: str) -> bool:
        raise NotImplementedError()

class InMemoryRateLimiter(BaseRateLimiter):
    """Simple in-memory rate limiter to pass TDD tests."""
    def __init__(self, limit: int = 5, window: float = 1.0):
        self.limit = limit
        self.window = window
        self.requests = {}

    def is_allowed(self, client_id: str) -> bool:
        now = time.time()
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        # Remove obsolete timestamps
        self.requests[client_id] = [req_time for req_time in self.requests[client_id] if now - req_time < self.window]
        
        if len(self.requests[client_id]) >= self.limit:
            return False
            
        self.requests[client_id].append(now)
        return True

class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, rate_limiter: BaseRateLimiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter

    async def dispatch(self, request: Request, call_next):
        # Allow metrics endpoint to bypass rate limiting (used by Prometheus)
        if request.url.path == "/metrics":
            return await call_next(request)

        # Extract client IP as identifier
        client_id = request.client.host if request.client else "127.0.0.1"
        
        if not self.rate_limiter.is_allowed(client_id):
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"}
            )
            
        return await call_next(request)
