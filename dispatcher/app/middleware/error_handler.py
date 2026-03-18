import logging
from abc import ABC, abstractmethod

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class BaseLogger(ABC):
    @abstractmethod
    def log_error(self, message: str, **kwargs) -> None:
        ...

    @abstractmethod
    def log_request(self, message: str, **kwargs) -> None:
        ...


class AppLogger(BaseLogger):
    def __init__(self, name: str = "dispatcher") -> None:
        self._logger = logging.getLogger(name)
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
            )
            self._logger.addHandler(handler)
            self._logger.setLevel(logging.INFO)

    def log_error(self, message: str, **kwargs) -> None:
        self._logger.error(message, extra=kwargs)

    def log_request(self, message: str, **kwargs) -> None:
        self._logger.info(message, extra=kwargs)


class BaseErrorHandler(ABC):
    @abstractmethod
    async def handle_exception(self, request: Request, exc: Exception) -> JSONResponse:
        ...


class ErrorHandler(BaseErrorHandler):
    def __init__(self, logger: BaseLogger) -> None:
        self._logger = logger

    async def handle_exception(self, request: Request, exc: Exception) -> JSONResponse:
        self._logger.log_error(
            f"{request.method} {request.url.path} - {type(exc).__name__}: {exc}"
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"},
        )


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, error_handler: BaseErrorHandler) -> None:
        super().__init__(app)
        self._error_handler = error_handler

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            return await self._error_handler.handle_exception(request, exc)
