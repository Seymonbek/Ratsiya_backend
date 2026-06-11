from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    DriverRegisterRequest,
    LoginRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse
from app.services.auth import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register/operator",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Operator yaratish",
)
async def register_operator(
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
async def register_driver(
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
async def login(
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
