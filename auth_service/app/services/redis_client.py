import os
import redis.asyncio as aioredis


class RedisClient:

    _instance: "RedisClient | None" = None
    _pool: aioredis.Redis | None = None

    def __init__(self) -> None:
        self._host = os.getenv("REDIS_HOST", "auth-redis")
        self._port = int(os.getenv("REDIS_PORT", "6379"))
        self._db = int(os.getenv("REDIS_DB", "0"))

    @classmethod
    async def get_instance(cls) -> aioredis.Redis:
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
        if cls._pool is not None:
            await cls._pool.close()
            cls._pool = None
            cls._instance = None
