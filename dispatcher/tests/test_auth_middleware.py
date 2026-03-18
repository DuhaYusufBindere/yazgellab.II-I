import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
import httpx

from app.main import app

@pytest.fixture
def client():
    """Senkron test istemcisi oluşturur."""
    return TestClient(app)

class TestAuthMiddleware:
    """
    Faz 3.B.1 - Auth Middleware Testleri (TDD RED Phase)
    """

    def test_missing_auth_header_returns_401(self, client):
        """Authorization header eksikse istek 401 Unauthorized dönmeli."""
        # /matches yetki gerektiren bir rotadır.
        response = client.get("/matches")
        
        # Henüz middleware yazılı olmadığı için bu test başarısız olacak
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Missing Authorization header"

    @patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    def test_valid_token_proceeds(self, mock_post, client):
        """Geçerli token ile istek işleme devam etmeli."""
        # Auth Service'e atılan token doğrulama isteği BAŞARILI (200 OK) dönüyor gibi simüle edelim.
        mock_post.return_value = httpx.Response(
            status_code=200, 
            json={"user_id": "123", "role": "user"},
            request=httpx.Request("POST", "http://auth-service:8001/auth/verify")
        )
        
        # İsteğin backend servisine iletildiğini doğrulamak için router'ı da mockluyoruz
        with patch("app.services.router.RouterService.forward_request", new_callable=AsyncMock) as mock_forward:
            mock_forward.return_value = httpx.Response(
                status_code=200, 
                json={"matches": []},
                request=httpx.Request("GET", "http://fake")
            )
            
            response = client.get("/matches", headers={"Authorization": "Bearer valid_token_abc"})
            
            assert response.status_code == 200
            mock_post.assert_called_once() # Auth service verification called
            mock_forward.assert_called_once() # Target service called

    @patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    def test_invalid_token_returns_401(self, mock_post, client):
        """Geçersiz token Auth Service tarafından 401 dönünce middleware 401 dönmeli."""
        # Auth Service token'ı geçersiz bulup 401 dönüyor
        mock_post.return_value = httpx.Response(
            status_code=401, 
            json={"detail": "Invalid token"},
            request=httpx.Request("POST", "http://auth-service:8001/auth/verify")
        )

        response = client.get("/matches", headers={"Authorization": "Bearer invalid_token"})

        assert response.status_code == 401
        assert "Invalid token" in str(response.json())

    @patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    def test_expired_token_returns_401(self, mock_post, client):
        """Süresi dolmuş token Auth Service tarafından 401 dönünce middleware 401 dönmeli."""
        # Auth Service token'ın süresi dolduğu için 401 dönüyor
        mock_post.return_value = httpx.Response(
            status_code=401, 
            json={"detail": "Token expired"},
            request=httpx.Request("POST", "http://auth-service:8001/auth/verify")
        )

        response = client.get("/matches", headers={"Authorization": "Bearer expired_token"})

        assert response.status_code == 401
        assert "Token expired" in str(response.json())

    def test_auth_routes_bypassed(self, client):
        """/auth ile başlayan rotalar token doğrulamasına (middleware'e) takılmamalı."""
        with patch("app.services.router.RouterService.forward_request", new_callable=AsyncMock) as mock_forward:
            mock_forward.return_value = httpx.Response(
                status_code=200, 
                json={"token": "abc"},
                request=httpx.Request("POST", "http://fake")
            )
            
            response = client.post("/auth/login", json={"username": "test", "password": "123"})
            
            # Auth servisine gidiyorsa middleware bloklamamalıdır
            assert response.status_code == 200
            mock_forward.assert_called_once()

    def test_health_check_bypassed(self, client):
        """/health rotası token doğrulamasına takılmamalı (public endpoint)."""
        response = client.get("/health")
        assert response.status_code == 200
