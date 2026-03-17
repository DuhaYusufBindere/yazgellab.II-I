import os
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

from jose import jwt, JWTError


class BaseTokenManager(ABC):

    @abstractmethod
    def create_token(self, data: dict) -> str:
        ...

    @abstractmethod
    def verify_token(self, token: str) -> dict | None:
        ...


class JWTTokenManager(BaseTokenManager):

    def __init__(
        self,
        secret_key: str | None = None,
        algorithm: str | None = None,
        expiration_minutes: int | None = None,
    ) -> None:
        self._secret_key = secret_key or os.getenv("SECRET_KEY", "change-me")
        self._algorithm = algorithm or os.getenv("JWT_ALGORITHM", "HS256")
        self._expiration_minutes = expiration_minutes or int(
            os.getenv("JWT_EXPIRATION_MINUTES", "30")
        )

    def create_token(self, data: dict) -> str:
        payload = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self._expiration_minutes)
        payload.update({"exp": expire, "jti": uuid.uuid4().hex})
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def verify_token(self, token: str) -> dict | None:
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
            return payload
        except JWTError:
            return None
