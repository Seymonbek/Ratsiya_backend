from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:

    @staticmethod
    async def create(
        db: AsyncSession,
        username: str,
        hashed_password: str,
        full_name: str,
        role: str,
    ) -> User:

        user = User(
            username=username,
            hashed_password=hashed_password,
            full_name=full_name,
            role=role,
        )
        db.add(user)
        await db.flush()    # INSERT bajariladi, ID generatsiya bo'ladi
        await db.refresh(user)  # DB dan to'liq ma'lumotni qayta o'qish
        return user

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> User | None:

        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_username(db: AsyncSession, username: str) -> User | None:

        result = await db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def exists_by_username(db: AsyncSession, username: str) -> bool:

        result = await db.execute(
            select(User.id).where(User.username == username)
        )
        return result.scalar_one_or_none() is not None


user_repository = UserRepository()
