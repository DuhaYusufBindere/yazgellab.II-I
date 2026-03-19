"""
Faz 3.A.1 – Dispatcher Routing Testleri (TDD RED Phase)

Bu test dosyası, Dispatcher'ın gelen istekleri URL yapısına göre doğru
mikroservise yönlendirmesini doğrular.

Yönlendirme Kuralları:
    /auth/**     → Auth Service    (http://auth-service:8001)
    /matches/**  → Match Service   (http://match-service:8002)
    /odds/**     → Betting Service (http://betting-service:8003)
    /users/**    → User Service    (http://user-service:8004)

TDD Notu: Bu testler henüz routing implementasyonu olmadığı için
           BAŞARISIZ olacaktır (RED aşaması).
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from httpx import Response

from app.main import app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def mock_auth_verify():
    """Tüm routing testleri için Auth doğrulamasını başarılı olarak (200 OK) mocklar."""
    with patch("app.middleware.auth.HttpTokenVerifier.verify_token", new_callable=AsyncMock) as mock_verify:
        mock_verify.return_value = True
        yield mock_verify


@pytest.fixture
def client():
    """Senkron test istemcisi oluşturur."""
    return TestClient(app)


def _mock_response(status_code: int = 200, json_body: dict | None = None) -> Response:
    """Mikroservislerden gelecek sahte HTTP yanıtı üretir."""
    import httpx
    body = json_body or {"status": "ok"}
    response = httpx.Response(
        status_code=status_code,
        json=body,
        request=httpx.Request("GET", "http://fake"),
    )
    return response


# 1. Temel Yönlendirme Testleri

class TestRouting:
    """Dispatcher'ın URL'ye göre doğru servise yönlendirmesini test eder."""

    @patch("app.services.router.RouterService.forward_request", new_callable=AsyncMock)
    def test_auth_route_forwards_to_auth_service(self, mock_forward, client):
        """
        /auth/login isteği Auth Service'e yönlendirilmeli.
        """
        mock_forward.return_value = _mock_response(200, {"token": "abc123"})

        response = client.post("/auth/login", json={"username": "test", "password": "1234"})

        assert response.status_code == 200
        mock_forward.assert_called_once()
        call_args = mock_forward.call_args
        # İlk argümanda hedef URL auth-service olmalı
        assert "auth-service" in str(call_args) or "8001" in str(call_args)

    @patch("app.services.router.RouterService.forward_request", new_callable=AsyncMock)
    def test_matches_route_forwards_to_match_service(self, mock_forward, client):
        """
        /matches isteği Match Service'e yönlendirilmeli.
        """
        mock_forward.return_value = _mock_response(200, {"matches": []})

        response = client.get("/matches", headers={"Authorization": "Bearer fake_token"})

        assert response.status_code == 200
        mock_forward.assert_called_once()
        call_args = mock_forward.call_args
        assert "match-service" in str(call_args) or "8002" in str(call_args)

    @patch("app.services.router.RouterService.forward_request", new_callable=AsyncMock)
    def test_single_match_route(self, mock_forward, client):
        """
        /matches/{id} isteği Match Service'e yönlendirilmeli.
        """
        mock_forward.return_value = _mock_response(200, {"id": "1", "home": "GS", "away": "FB"})

        response = client.get("/matches/1", headers={"Authorization": "Bearer fake_token"})

        assert response.status_code == 200
        mock_forward.assert_called_once()

    @patch("app.services.router.RouterService.forward_request", new_callable=AsyncMock)
    def test_odds_route_forwards_to_betting_service(self, mock_forward, client):
        """
        /odds isteği Betting Service'e yönlendirilmeli.
        """
        mock_forward.return_value = _mock_response(200, {"odds": []})

        response = client.get("/odds", headers={"Authorization": "Bearer fake_token"})

        assert response.status_code == 200
        mock_forward.assert_called_once()
        call_args = mock_forward.call_args
        assert "betting-service" in str(call_args) or "8003" in str(call_args)

    @patch("app.services.router.RouterService.forward_request", new_callable=AsyncMock)
    def test_users_route_forwards_to_user_service(self, mock_forward, client):
        """
        /users/{id}/favorites isteği User Service'e yönlendirilmeli.
        """
        mock_forward.return_value = _mock_response(200, {"favorites": []})

        response = client.get("/users/42/favorites", headers={"Authorization": "Bearer fake_token"})

        assert response.status_code == 200
        mock_forward.assert_called_once()
        call_args = mock_forward.call_args
        assert "user-service" in str(call_args) or "8004" in str(call_args)


# 2. HTTP Metotları Testleri 

class TestHTTPMethods:
    """Her HTTP metodunun doğru şekilde yönlendirildiğini test eder."""

    @patch("app.services.router.RouterService.forward_request", new_callable=AsyncMock)
    def test_post_request_forwarded(self, mock_forward, client):
        """POST metodu korunarak hedef servise iletilmeli."""
        mock_forward.return_value = _mock_response(201, {"id": "new-match"})

        response = client.post("/matches", json={"home": "GS", "away": "FB"}, headers={"Authorization": "Bearer fake_token"})

        assert response.status_code == 201
        mock_forward.assert_called_once()

    @patch("app.services.router.RouterService.forward_request", new_callable=AsyncMock)
    def test_put_request_forwarded(self, mock_forward, client):
        """PUT metodu korunarak hedef servise iletilmeli."""
        mock_forward.return_value = _mock_response(200, {"updated": True})

        response = client.put("/matches/1", json={"home_score": 2, "away_score": 1}, headers={"Authorization": "Bearer fake_token"})

        assert response.status_code == 200
        mock_forward.assert_called_once()

    @patch("app.services.router.RouterService.forward_request", new_callable=AsyncMock)
    def test_delete_request_forwarded(self, mock_forward, client):
        """DELETE metodu korunarak hedef servise iletilmeli."""
        mock_forward.return_value = _mock_response(204)

        response = client.delete("/matches/1", headers={"Authorization": "Bearer fake_token"})

        assert response.status_code == 204
        mock_forward.assert_called_once()


# 3. Bilinmeyen Route Testleri

class TestUnknownRoutes:
    """Tanımsız URL'lerin 404 döndürdüğünü test eder."""

    def test_unknown_route_returns_404(self, client):
        """
        Hiçbir servise eşleşmeyen URL'ler 404 Not Found döndürmeli.
        """
        response = client.get("/nonexistent/endpoint", headers={"Authorization": "Bearer fake_token"})

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data or "error" in data

    def test_root_path_returns_info_or_404(self, client):
        """
        Kök URL (/) bir bilgi mesajı veya 404 dönmeli.
        """
        response = client.get("/", headers={"Authorization": "Bearer fake_token"})

        # Kök endpoint ya bilgi döndürür ya da 404
        assert response.status_code in (200, 404)


# 4. Health Check Testi

class TestHealthCheck:
    """Dispatcher health endpoint'inin çalıştığını doğrular."""

    def test_health_endpoint_returns_ok(self, client):
        """
        /health endpoint'i 200 OK ve status: ok döndürmeli.
        """
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "dispatcher"


class TestServiceRegistry:
    """
    Somut ServiceRegistry sınıfının BaseServiceRegistry arayüzünü
    doğru bir şekilde implemente ettiğini test eder.
    """

    def test_registry_is_subclass_of_base(self):
        """ServiceRegistry, BaseServiceRegistry alt sınıfı olmalı (OOP)."""
        from app.services.router import ServiceRegistry, BaseServiceRegistry
        assert issubclass(ServiceRegistry, BaseServiceRegistry)

    def test_registry_has_all_services(self):
        """
        ServiceRegistry en az 4 servisi (auth, match, betting, user) içermeli.
        """
        from app.services.router import ServiceRegistry

        registry = ServiceRegistry()

        assert registry.get_service_url("auth") is not None
        assert registry.get_service_url("matches") is not None
        assert registry.get_service_url("odds") is not None
        assert registry.get_service_url("users") is not None

    def test_registry_returns_none_for_unknown_service(self):
        """
        Bilinmeyen bir servis adı için None döndürmeli.
        """
        from app.services.router import ServiceRegistry

        registry = ServiceRegistry()

        assert registry.get_service_url("nonexistent") is None

    def test_registry_returns_correct_urls(self):
        """
        Her servis için doğru URL döndürmeli.
        """
        from app.services.router import ServiceRegistry

        registry = ServiceRegistry()

        auth_url = registry.get_service_url("auth")
        assert "8001" in auth_url

        match_url = registry.get_service_url("matches")
        assert "8002" in match_url

        betting_url = registry.get_service_url("odds")
        assert "8003" in betting_url

        user_url = registry.get_service_url("users")
        assert "8004" in user_url


# 6. RouterService 

class TestRouterServiceOOP:
    """
    RouterService'in BaseRouterService arayüzünü doğru şekilde
    implemente ettiğini ve Dependency Injection ile çalıştığını test eder.
    """

    def test_router_service_is_subclass_of_base(self):
        """RouterService, BaseRouterService alt sınıfı olmalı (OOP)."""
        from app.services.router import RouterService, BaseRouterService
        assert issubclass(RouterService, BaseRouterService)

    def test_router_service_requires_registry(self):
        """RouterService, constructor'da bir BaseServiceRegistry beklemeli (DIP)."""
        from app.services.router import RouterService, ServiceRegistry
        registry = ServiceRegistry()
        router = RouterService(registry=registry)
        assert router._registry is registry

    def test_resolve_target_url_returns_correct_url(self):
        """resolve_target_url doğru tam URL'yi oluşturmalı."""
        from app.services.router import RouterService, ServiceRegistry
        registry = ServiceRegistry()
        router = RouterService(registry=registry)

        url = router.resolve_target_url("auth/login")
        assert url is not None
        assert "auth-service" in url or "8001" in url
        assert "auth/login" in url

    def test_resolve_target_url_returns_none_for_unknown(self):
        """Bilinmeyen path için resolve_target_url None döndürmeli."""
        from app.services.router import RouterService, ServiceRegistry
        registry = ServiceRegistry()
        router = RouterService(registry=registry)

        url = router.resolve_target_url("unknown/endpoint")
        assert url is None

    def test_resolve_target_url_returns_none_for_empty(self):
        """Boş path için resolve_target_url None döndürmeli."""
        from app.services.router import RouterService, ServiceRegistry
        registry = ServiceRegistry()
        router = RouterService(registry=registry)

        url = router.resolve_target_url("")
        assert url is None
