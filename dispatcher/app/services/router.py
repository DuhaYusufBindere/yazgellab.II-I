"""
Dispatcher – Router Modülü (OOP / SOLID Uyumlu)

Soyutlamalar (Abstract Base Classes):
    - BaseServiceRegistry : Servis kayıt defteri arayüzü
    - BaseRouterService   : İstek yönlendirme arayüzü

Somut Sınıflar:
    - ServiceRegistry     : Ortam değişkenlerinden URL okuyan kayıt defteri
    - RouterService       : httpx ile istekleri mikroservislere ileten yönlendirici
"""

import os
import logging
from abc import ABC, abstractmethod

import httpx
from fastapi import Request


# ---------------------------------------------------------------------------
# Soyut Sınıflar (Interfaces / Abstraction)
# ---------------------------------------------------------------------------

class BaseServiceRegistry(ABC):
    """
    Mikroservis URL'lerini sağlayan soyut temel sınıf.

    Alt sınıflar, `get_service_url` metodunu uygulayarak
    servis-adı → URL eşlemesini döndürmelidir.
    """

    @abstractmethod
    def get_service_url(self, service_name: str) -> str | None:
        """Verilen servis adına karşılık gelen base URL'yi döndürür; bulunamazsa None."""
        ...


class BaseRouterService(ABC):
    """
    İstek yönlendirme işlemlerinin sözleşmesini tanımlayan soyut sınıf.

    Alt sınıflar:
        - `resolve_target_url`  : Path → hedef URL dönüşümü
        - `forward_request`     : İsteği hedef servise iletme
    """

    def __init__(self, registry: BaseServiceRegistry) -> None:
        """
        Args:
            registry: Servis adreslerini çözmek için kullanılan kayıt defteri.
                      (Dependency Inversion – somut sınıf yerine soyutlamaya bağımlılık)
        """
        self._registry = registry

    @abstractmethod
    def resolve_target_url(self, path: str) -> str | None:
        """URL path'inden hedef servisin tam adresini döndürür; eşleşme yoksa None."""
        ...

    @abstractmethod
    async def forward_request(self, target_url: str, request: Request) -> httpx.Response | None:
        """HTTP isteğini hedef servise iletir ve yanıtı döndürür; hata olursa None."""
        ...


# ---------------------------------------------------------------------------
# Somut Sınıflar (Concrete Implementations)
# ---------------------------------------------------------------------------

class ServiceRegistry(BaseServiceRegistry):
    """
    Ortam değişkenlerinden servis URL'lerini okuyan somut kayıt defteri.

    Varsayılan olarak Docker Compose servis adlarını kullanır.
    """

    def __init__(self) -> None:
        self._services: dict[str, str] = {
            "auth":    os.getenv("AUTH_SERVICE_URL",    "http://auth-service:8001"),
            "matches": os.getenv("MATCH_SERVICE_URL",   "http://match-service:8002"),
            "odds":    os.getenv("BETTING_SERVICE_URL",  "http://betting-service:8003"),
            "users":   os.getenv("USER_SERVICE_URL",    "http://user-service:8004"),
        }

    def get_service_url(self, service_name: str) -> str | None:
        """Servis adına karşılık gelen base URL'yi döndürür."""
        return self._services.get(service_name)


class RouterService(BaseRouterService):
    """
    Gelen HTTP isteklerini ilgili mikroservise ileten somut yönlendirici.

    Dependency Injection:
        - `registry`    : Servis URL çözümlemesi (BaseServiceRegistry)
        - `http_client` : Opsiyonel harici httpx.AsyncClient (test ve connection-pool)
    """

    def __init__(
        self,
        registry: BaseServiceRegistry,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(registry)
        self._http_client = http_client
        self._logger = logging.getLogger(self.__class__.__name__)

    # -- URL Çözümleme -------------------------------------------------------

    def resolve_target_url(self, path: str) -> str | None:
        """
        URL path'inin ilk segmentine göre hedef servisin tam adresini oluşturur.

        Örnek: "auth/login" → "http://auth-service:8001/auth/login"
        """
        parts = path.strip("/").split("/")
        if not parts or not parts[0]:
            return None

        service_name = parts[0]
        base_url = self._registry.get_service_url(service_name)

        if base_url is None:
            return None

        return f"{base_url}/{path.strip('/')}"

    # -- İstek Yönlendirme ---------------------------------------------------

    async def forward_request(
        self, target_url: str, request: Request
    ) -> httpx.Response | None:
        """
        HTTP isteğini hedef URL'ye iletir.

        Eğer constructor'dan bir `http_client` enjekte edilmişse onu kullanır;
        aksi halde tek seferlik bir AsyncClient oluşturur ve kapatır.
        """
        method = request.method
        headers = dict(request.headers)
        headers.pop("host", None)           # Kendi host başlığımızı göndermiyoruz
        body = await request.body()

        # Enjekte edilen client yoksa geçici client aç
        owns_client = self._http_client is None
        client = self._http_client or httpx.AsyncClient(follow_redirects=True)

        try:
            response = await client.request(
                method=method,
                url=target_url,
                headers=headers,
                content=body,
            )
            return response
        except httpx.RequestError as exc:
            self._logger.error("Router request failed to %s: %s", target_url, exc)
            return None
        finally:
            if owns_client:
                await client.aclose()
