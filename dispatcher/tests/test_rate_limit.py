import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

class TestRateLimiter:
    """
    Faz 3.D.1 - Rate Limiting Testleri (TDD RED Phase)
    """

    def test_rate_limit_exceeded_returns_429(self, client):
        """Eşik değeri aşıldığında istek 429 Too Many Requests dönmeli."""
        
        # Saniyede 5 istek limiti olduğunu varsayıyoruz. 
        # İlk 5 istek başarılı geçmeli.
        for _ in range(5):
            response = client.get("/health")
            assert response.status_code == 200

        # 6. istek eşiği aştığı için rate limiter tarafından bloklanmalı
        # Şu an rate limiter yazılımadığı için bu beklenen şekilde 429 dönmeyecek ve test kızaracak (RED).
        response = client.get("/health")
        assert response.status_code == 429
        
        data = response.json()
        assert "detail" in data
        assert "Rate limit exceeded" in data["detail"]
