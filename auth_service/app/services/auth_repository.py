import json
from abc import ABC, abstractmethod
from datetime import datetime

from passlib.context import CryptContext

from app.models.user import User


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class BaseAuthRepository(ABC):

    @abstractmethod
    async def save_user(self, user: User) -> bool:
        ...

    @abstractmethod
    async def get_user(self, username: str) -> User | None:
        ...

    @abstractmethod
    async def user_exists(self, username: str) -> bool:
        ...

    @abstractmethod
    async def save_token(self, jti: str, username: str, ttl_seconds: int) -> None:
        ...

    @abstractmethod
    async def delete_token(self, jti: str) -> None:
        ...

    @abstractmethod
    async def is_token_valid(self, jti: str) -> bool:
        ...


class RedisAuthRepository(BaseAuthRepository):

    def __init__(self, redis_client) -> None:
        self._redis = redis_client

    async def save_user(self, user: User) -> bool:
        key = f"user:{user.username}"
        data = {
            "username": user.username,
            "hashed_password": user.hashed_password,
            "role": user.role,
            "created_at": user.created_at.isoformat(),
        }
        await self._redis.set(key, json.dumps(data))
        return True

    async def get_user(self, username: str) -> User | None:
        key = f"user:{username}"
        raw = await self._redis.get(key)
        if raw is None:
            return None
        data = json.loads(raw)
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return User(**data)

    async def user_exists(self, username: str) -> bool:
        return await self._redis.exists(f"user:{username}") > 0

    async def save_token(self, jti: str, username: str, ttl_seconds: int) -> None:
        await self._redis.set(f"token:{jti}", username, ex=ttl_seconds)

    async def delete_token(self, jti: str) -> None:
        await self._redis.delete(f"token:{jti}")

    async def is_token_valid(self, jti: str) -> bool:
        return await self._redis.exists(f"token:{jti}") > 0


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
