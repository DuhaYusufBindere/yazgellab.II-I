import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

class TestMetrics:
    """
    Faz 3.D.4 - Metrics Testleri (TDD RED Phase)
    """

    def test_metrics_endpoint_returns_prometheus_format(self, client):
        """/metrics endpoint'i çağrıldığında Prometheus formatında metrikler dönmeli."""
        
        # Henüz /metrics rotası yazılmadığı için 404 dönecektir (RED).
        response = client.get("/metrics")
        
        # Başarılı olduğunda 200 dönmeli
        assert response.status_code == 200
        
        # Prometheus çıktıları genellikle metin bazlıdır
        assert "text/plain" in response.headers.get("content-type", "").lower()
        
        # Çıktı içerisinde Prometheus loglarına ait anahtar kelimeler olmalı
        # (Örneğin framework tarafındaki standart metrikler veya custom request_count gibi)
        assert ("python_" in response.text or "http_request_" in response.text)
