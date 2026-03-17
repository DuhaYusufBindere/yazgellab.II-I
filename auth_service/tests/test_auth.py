import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from app.models.user import User, UserCreate, UserLogin, TokenVerifyRequest
from app.services.token_manager import JWTTokenManager, BaseTokenManager
from app.services.auth_repository import (
    BaseAuthRepository,
    RedisAuthRepository,
    hash_password,
    verify_password,
)


# ---------------------------------------------------------------------------
# TokenManager Testleri
# ---------------------------------------------------------------------------

class TestJWTTokenManager:

    def setup_method(self):
        self.manager = JWTTokenManager(
            secret_key="test-secret",
            algorithm="HS256",
            expiration_minutes=30,
        )

    def test_is_subclass_of_base(self):
        assert issubclass(JWTTokenManager, BaseTokenManager)

    def test_create_token_returns_string(self):
        token = self.manager.create_token({"sub": "testuser", "role": "user"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_valid_token(self):
        token = self.manager.create_token({"sub": "testuser", "role": "user"})
        payload = self.manager.verify_token(token)
        assert payload is not None
        assert payload["sub"] == "testuser"
        assert payload["role"] == "user"
        assert "jti" in payload
        assert "exp" in payload

    def test_verify_invalid_token_returns_none(self):
        result = self.manager.verify_token("invalid.token.string")
        assert result is None

    def test_verify_wrong_secret_returns_none(self):
        token = self.manager.create_token({"sub": "testuser"})
        other_manager = JWTTokenManager(secret_key="wrong-secret")
        result = other_manager.verify_token(token)
        assert result is None

    def test_each_token_has_unique_jti(self):
        t1 = self.manager.create_token({"sub": "user1"})
        t2 = self.manager.create_token({"sub": "user1"})
        p1 = self.manager.verify_token(t1)
        p2 = self.manager.verify_token(t2)
        assert p1["jti"] != p2["jti"]


# ---------------------------------------------------------------------------
# Password Hash Testleri
# ---------------------------------------------------------------------------

class TestPasswordHashing:

    def test_hash_password_returns_different_from_plain(self):
        hashed = hash_password("mypassword")
        assert hashed != "mypassword"

    def test_verify_correct_password(self):
        hashed = hash_password("mypassword")
        assert verify_password("mypassword", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("mypassword")
        assert verify_password("wrongpassword", hashed) is False


# ---------------------------------------------------------------------------
# RedisAuthRepository Testleri
# ---------------------------------------------------------------------------

class TestRedisAuthRepository:

    def setup_method(self):
        self.mock_redis = AsyncMock()
        self.repo = RedisAuthRepository(self.mock_redis)

    @pytest.mark.asyncio
    async def test_is_subclass_of_base(self):
        assert issubclass(RedisAuthRepository, BaseAuthRepository)

    @pytest.mark.asyncio
    async def test_save_user(self):
        user = User(
            username="testuser",
            hashed_password="hashed123",
            role="user",
            created_at=datetime(2026, 1, 1),
        )
        result = await self.repo.save_user(user)
        assert result is True
        self.mock_redis.set.assert_called_once()
        call_key = self.mock_redis.set.call_args[0][0]
        assert call_key == "user:testuser"

    @pytest.mark.asyncio
    async def test_get_user_found(self):
        import json
        user_data = json.dumps({
            "username": "testuser",
            "hashed_password": "hashed123",
            "role": "user",
            "created_at": "2026-01-01T00:00:00",
        })
        self.mock_redis.get.return_value = user_data

        user = await self.repo.get_user("testuser")
        assert user is not None
        assert user.username == "testuser"
        assert user.role == "user"

    @pytest.mark.asyncio
    async def test_get_user_not_found(self):
        self.mock_redis.get.return_value = None
        user = await self.repo.get_user("nonexistent")
        assert user is None

    @pytest.mark.asyncio
    async def test_user_exists_true(self):
        self.mock_redis.exists.return_value = 1
        result = await self.repo.user_exists("testuser")
        assert result is True

    @pytest.mark.asyncio
    async def test_user_exists_false(self):
        self.mock_redis.exists.return_value = 0
        result = await self.repo.user_exists("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_save_token(self):
        await self.repo.save_token("jti123", "testuser", 1800)
        self.mock_redis.set.assert_called_once_with("token:jti123", "testuser", ex=1800)

    @pytest.mark.asyncio
    async def test_delete_token(self):
        await self.repo.delete_token("jti123")
        self.mock_redis.delete.assert_called_once_with("token:jti123")

    @pytest.mark.asyncio
    async def test_is_token_valid_true(self):
        self.mock_redis.exists.return_value = 1
        result = await self.repo.is_token_valid("jti123")
        assert result is True

    @pytest.mark.asyncio
    async def test_is_token_valid_false(self):
        self.mock_redis.exists.return_value = 0
        result = await self.repo.is_token_valid("jti123")
        assert result is False


# ---------------------------------------------------------------------------
# Pydantic Model Testleri
# ---------------------------------------------------------------------------

class TestUserModels:

    def test_user_create_valid(self):
        uc = UserCreate(username="testuser", password="1234")
        assert uc.username == "testuser"

    def test_user_create_short_username_raises(self):
        with pytest.raises(Exception):
            UserCreate(username="ab", password="1234")

    def test_user_create_short_password_raises(self):
        with pytest.raises(Exception):
            UserCreate(username="testuser", password="12")

    def test_user_default_role(self):
        user = User(username="test", hashed_password="hash123")
        assert user.role == "user"

    def test_token_verify_request(self):
        req = TokenVerifyRequest(token="some.jwt.token")
        assert req.token == "some.jwt.token"
