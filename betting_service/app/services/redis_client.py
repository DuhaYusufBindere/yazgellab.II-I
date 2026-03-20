"""Betting Service – Redis bağlantı yöneticisi (Singleton).

auth_service ile aynı pattern kullanılır. Ortam değişkenlerinden
bağlantı bilgisi okunur ve tek bir bağlantı havuzu yönetilir.
"""

import os

import redis.asyncio as aioredis


class RedisClient:
    """Betting-Redis için async bağlantı havuzunu yöneten Singleton sınıf.

    Prensipte tek bir Redis bağlantısı tüm uygulama boyunca paylaşılır
    (Singleton Pattern). ``get_instance`` ile bağlantı elde edilir,
    ``close`` ile uygulama kapanırken serbest bırakılır.
    """

    _instance: "RedisClient | None" = None
    _pool: aioredis.Redis | None = None

    def __init__(self) -> None:
        self._host = os.getenv("REDIS_HOST", "betting-redis")
        self._port = int(os.getenv("REDIS_PORT", "6379"))
        self._db = int(os.getenv("REDIS_DB", "0"))

    @classmethod
    async def get_instance(cls) -> aioredis.Redis:
        """Mevcut Redis bağlantı havuzunu döndürür, yoksa oluşturur."""
        if cls._pool is None:
            client = cls()
            cls._pool = aioredis.Redis(
                host=client._host,
                port=client._port,
                db=client._db,
                decode_responses=True,
            )
            cls._instance = client
        return cls._pool

    @classmethod
    async def close(cls) -> None:
        """Redis bağlantısını kapatır ve singleton referansını temizler."""
        if cls._pool is not None:
            await cls._pool.close()
            cls._pool = None
            cls._instance = None
