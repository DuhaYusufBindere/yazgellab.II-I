from fastapi import APIRouter, HTTPException, status

from app.models.user import (
    UserCreate,
    UserLogin,
    User,
    TokenResponse,
    TokenVerifyRequest,
    TokenVerifyResponse,
)
from app.services.auth_repository import (
    RedisAuthRepository,
    hash_password,
    verify_password,
)
from app.services.token_manager import JWTTokenManager
from app.services.redis_client import RedisClient

router = APIRouter(prefix="/auth", tags=["auth"])

token_manager = JWTTokenManager()


async def _get_repo() -> RedisAuthRepository:
    redis = await RedisClient.get_instance()
    return RedisAuthRepository(redis)


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=dict)
async def register(body: UserCreate):
    repo = await _get_repo()

    if await repo.user_exists(body.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    user = User(
        username=body.username,
        hashed_password=hash_password(body.password),
    )
    await repo.save_user(user)
    return {"message": "User registered successfully", "username": user.username}


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin):
    repo = await _get_repo()
    user = await repo.get_user(body.username)

    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = token_manager.create_token(
        {"sub": user.username, "role": user.role}
    )

    payload = token_manager.verify_token(token)
    if payload and "jti" in payload:
        ttl = 30 * 60
        await repo.save_token(payload["jti"], user.username, ttl)

    return TokenResponse(access_token=token)


@router.post("/verify", response_model=TokenVerifyResponse)
async def verify(body: TokenVerifyRequest):
    repo = await _get_repo()
    payload = token_manager.verify_token(body.token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    jti = payload.get("jti")
    if jti and not await repo.is_token_valid(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )

    return TokenVerifyResponse(
        valid=True,
        username=payload.get("sub"),
        role=payload.get("role"),
    )


@router.delete("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: TokenVerifyRequest):
    payload = token_manager.verify_token(body.token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    jti = payload.get("jti")
    if jti:
        repo = await _get_repo()
        await repo.delete_token(jti)

    return None
