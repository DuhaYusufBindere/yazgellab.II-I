import pytest
from app.main import rate_limiter

@pytest.fixture(autouse=True)
def reset_rate_limiter_state():
    """
    TDD PRENSİBİ (TEST İZOLASYONU):
    Her testten önce Rate Limiter'ın hafızasındaki istek sayısını sıfırlar.
    Böylece bir testteki 5 istek limiti, diğer testleri kilitlemez (State Leak engellenir).
    """
    rate_limiter.requests.clear()
