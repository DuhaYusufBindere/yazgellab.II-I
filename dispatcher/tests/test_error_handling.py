"""
Faz 3.C.1 – Dispatcher Error Handling Testleri (RED)

Dispatcher'in hata durumlarini test eder:
    404, 502, 401, 500 senaryolari
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
import httpx

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1. ErrorHandler & Logger OOP Testleri
# ---------------------------------------------------------------------------

class TestErrorHandlerOOP:

    def test_error_handler_is_subclass_of_base(self):
        from app.middleware.error_handler import ErrorHandler, BaseErrorHandler
        assert issubclass(ErrorHandler, BaseErrorHandler)

    def test_logger_is_subclass_of_base(self):
        from app.middleware.error_handler import AppLogger, BaseLogger
        assert issubclass(AppLogger, BaseLogger)

    def test_error_handler_has_handle_method(self):
        from app.middleware.error_handler import ErrorHandler
        assert hasattr(ErrorHandler, "handle_exception")

    def test_logger_has_log_method(self):
        from app.middleware.error_handler import AppLogger
        logger = AppLogger()
        assert callable(getattr(logger, "log_error", None))


# ---------------------------------------------------------------------------
# 2. HTTP 500 – Beklenmeyen Sunucu Hatası
# ---------------------------------------------------------------------------

class TestInternalServerError:

    @patch("app.services.router.RouterService.forward_request", new_callable=AsyncMock)
    @patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    def test_unhandled_exception_returns_500(self, mock_auth, mock_forward, client):
        """Beklenmeyen hata durumunda 500 Internal Server Error dönmeli."""
        mock_auth.return_value = httpx.Response(
            status_code=200,
            json={"valid": True, "username": "test", "role": "user"},
            request=httpx.Request("POST", "http://auth-service:8001/auth/verify"),
        )
        mock_forward.side_effect = RuntimeError("Unexpected internal error")

        response = client.get("/matches", headers={"Authorization": "Bearer valid_token"})

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data

    @patch("app.services.router.RouterService.forward_request", new_callable=AsyncMock)
    @patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    def test_500_response_format(self, mock_auth, mock_forward, client):
        """500 yanıtı tutarlı JSON formatında olmalı."""
        mock_auth.return_value = httpx.Response(
            status_code=200,
            json={"valid": True, "username": "test", "role": "user"},
            request=httpx.Request("POST", "http://auth-service:8001/auth/verify"),
        )
        mock_forward.side_effect = Exception("Something broke")

        response = client.get("/matches", headers={"Authorization": "Bearer valid_token"})

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)


# ---------------------------------------------------------------------------
# 3. HTTP 404 – Tanımsız Route
# ---------------------------------------------------------------------------

class TestNotFoundError:

    @patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    def test_unknown_route_returns_404_json(self, mock_auth, client):
        """Bilinmeyen URL 404 ve JSON hata mesajı dönmeli."""
        mock_auth.return_value = httpx.Response(
            status_code=200,
            json={"valid": True, "username": "test", "role": "user"},
            request=httpx.Request("POST", "http://auth-service:8001/auth/verify"),
        )
        response = client.get("/nonexistent/path",
                              headers={"Authorization": "Bearer valid_token"})
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    @patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    def test_404_has_proper_detail(self, mock_auth, client):
        """404 yanıtında açıklayıcı mesaj olmalı."""
        mock_auth.return_value = httpx.Response(
            status_code=200,
            json={"valid": True, "username": "test", "role": "user"},
            request=httpx.Request("POST", "http://auth-service:8001/auth/verify"),
        )
        response = client.get("/completely/unknown",
                              headers={"Authorization": "Bearer valid_token"})
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# 4. HTTP 502 – Servis Ulaşılamaz
# ---------------------------------------------------------------------------

class TestBadGatewayError:

    @patch("app.services.router.RouterService.forward_request", new_callable=AsyncMock)
    @patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    def test_service_unavailable_returns_502(self, mock_auth, mock_forward, client):
        """Mikroservis ulaşılamaz durumda 502 Bad Gateway dönmeli."""
        mock_auth.return_value = httpx.Response(
            status_code=200,
            json={"valid": True, "username": "test", "role": "user"},
            request=httpx.Request("POST", "http://auth-service:8001/auth/verify"),
        )
        mock_forward.return_value = None

        response = client.get("/matches", headers={"Authorization": "Bearer valid_token"})

        assert response.status_code == 502
        data = response.json()
        assert "detail" in data

    @patch("app.services.router.RouterService.forward_request", new_callable=AsyncMock)
    @patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    def test_502_json_format(self, mock_auth, mock_forward, client):
        """502 yanıtı tutarlı JSON formatında olmalı."""
        mock_auth.return_value = httpx.Response(
            status_code=200,
            json={"valid": True, "username": "test", "role": "user"},
            request=httpx.Request("POST", "http://auth-service:8001/auth/verify"),
        )
        mock_forward.return_value = None

        response = client.get("/odds", headers={"Authorization": "Bearer valid_token"})

        assert response.status_code == 502
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)


# ---------------------------------------------------------------------------
# 5. HTTP 401 – Yetkisiz Erişim (ErrorHandler üzerinden)
# ---------------------------------------------------------------------------

class TestUnauthorizedError:

    def test_missing_token_returns_401(self, client):
        """Token olmadan korumalı endpoint'e istek 401 dönmeli."""
        response = client.get("/matches")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    def test_invalid_token_returns_401(self, mock_auth, client):
        """Geçersiz token ile istek 401 dönmeli."""
        mock_auth.return_value = httpx.Response(
            status_code=401,
            json={"detail": "Invalid token"},
            request=httpx.Request("POST", "http://auth-service:8001/auth/verify"),
        )
        response = client.get("/matches", headers={"Authorization": "Bearer bad_token"})
        assert response.status_code == 401
