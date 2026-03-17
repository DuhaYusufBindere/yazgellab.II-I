from fastapi import Request

class ServiceRegistry:
    def __init__(self):
        self._services = {
            "auth": "http://auth-service:8001",
            "matches": "http://match-service:8002",
            "odds": "http://betting-service:8003",
            "users": "http://user-service:8004"
        }

    def get_service_url(self, service_name: str) -> str | None:
        return self._services.get(service_name)

class RouterService:
    async def forward_request(self, target_url: str, request: Request):
        """
        Gelen istekleri ilgili mikroservise ileten temel metot.
        TDD'nin Red -> Green aşamasında bu metot birim testlerde mocklanarak test ediliyor.
        Gerçek implementasyon ilerleyen fazlarda eklenecek.
        """
        return None
