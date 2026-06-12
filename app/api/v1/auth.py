from fastapi import APIRouter, Depends, status, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.security import decode_access_token
from app.dependencies.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.redis.token_blacklist import revoke_token
from app.schemas.auth import (
    RegisterRequest,
    DriverRegisterRequest,
    LoginRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse
from app.services.auth import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

_logout_scheme = HTTPBearer()


@router.post(
    "/register/operator",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Operator yaratish",
)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def register_operator(
    request: Request,
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):

    user = await auth_service.register_operator(
        db=db,
        username=data.username,
        password=data.password,
        full_name=data.full_name,
    )
    return user


@router.post(
    "/register/driver",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Driver yaratish",
)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def register_driver(
    request: Request,
    data: DriverRegisterRequest,
    db: AsyncSession = Depends(get_db),
):

    user = await auth_service.register_driver(
        db=db,
        username=data.username,
        password=data.password,
        full_name=data.full_name,
        license_plate=data.license_plate,
    )
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Tizimga kirish",
)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def login(
    request: Request,
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):

    token = await auth_service.login(
        db=db,
        username=data.username,
        password=data.password,
    )
    return TokenResponse(access_token=token)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Hozirgi foydalanuvchi",
)
async def get_me(
    current_user: User = Depends(get_current_user),
):

    return current_user


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Tizimdan chiqish (tokenni bekor qilish)",
)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(_logout_scheme),
    current_user: User = Depends(get_current_user),
):

    payload = decode_access_token(credentials.credentials)
    if payload is not None:
        jti = payload.get("jti")
        exp = payload.get("exp")
        if jti and exp:
            await revoke_token(jti, int(exp))
    return {"detail": "Tizimdan muvaffaqiyatli chiqildi"}
