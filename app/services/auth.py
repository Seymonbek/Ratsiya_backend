from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import setup_logger
from app.core.security import hash_password, verify_password, create_access_token
from app.enums import UserRole
from app.models.user import User
from app.repositories.user import user_repository
from app.repositories.driver import driver_repository

logger = setup_logger(__name__)


class AuthService:
    """Autentifikatsiya servisi."""

    @staticmethod
    async def register_operator(
        db: AsyncSession,
        username: str,
        password: str,
        full_name: str,
    ) -> User:

        # 1. Username band emasligini tekshirish
        if await user_repository.exists_by_username(db, username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"'{username}' allaqachon band",
            )

        # 2. Parolni hash qilish
        hashed = hash_password(password)

        # 3. Operator yaratish
        user = await user_repository.create(
            db=db,
            username=username,
            hashed_password=hashed,
            full_name=full_name,
            role=UserRole.OPERATOR,
        )

        logger.info(f"Operator yaratildi: {username}")
        return user

    @staticmethod
    async def register_driver(
        db: AsyncSession,
        username: str,
        password: str,
        full_name: str,
        license_plate: str,
    ) -> User:

        # 1. Username tekshirish
        if await user_repository.exists_by_username(db, username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"'{username}' allaqachon band",
            )

        # 2. User yaratish (driver roli bilan)
        hashed = hash_password(password)
        user = await user_repository.create(
            db=db,
            username=username,
            hashed_password=hashed,
            full_name=full_name,
            role=UserRole.DRIVER,
        )

        # 3. Driver profili yaratish
        await driver_repository.create(
            db=db,
            user_id=user.id,
            license_plate=license_plate,
        )

        logger.info(f"Driver yaratildi: {username} ({license_plate})")
        return user

    @staticmethod
    async def login(
        db: AsyncSession,
        username: str,
        password: str,
    ) -> str:

        # 1. User'ni topish
        user = await user_repository.get_by_username(db, username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Login yoki parol noto'g'ri",
            )

        # 2. Parolni tekshirish
        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Login yoki parol noto'g'ri",
            )

        # 3. Account faolmi
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Foydalanuvchi hisobi o'chirilgan",
            )

        # 4. Token yaratish
        token = create_access_token(user_id=user.id, role=user.role)
        logger.info(f"Foydalanuvchi tizimga kirdi: {username}")
        return token


auth_service = AuthService()
