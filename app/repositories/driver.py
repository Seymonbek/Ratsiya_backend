from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.driver import Driver
from app.enums import DriverStatus


class DriverRepository:
    """Haydovchi repository."""

    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: int,
        license_plate: str,
    ) -> Driver:

        driver = Driver(
            user_id=user_id,
            license_plate=license_plate,
            status=DriverStatus.OFFLINE,  # Boshlang'ich — offline
        )
        db.add(driver)
        await db.flush()
        await db.refresh(driver)
        return driver

    @staticmethod
    async def get_by_id(db: AsyncSession, driver_id: int) -> Driver | None:
        """ID bo'yicha driverni topish (User ma'lumoti bilan)."""
        result = await db.execute(
            select(Driver)
            .options(joinedload(Driver.user))  # User'ni ham yuklash (1 ta query)
            .where(Driver.id == driver_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_user_id(db: AsyncSession, user_id: int) -> Driver | None:
        """User ID bo'yicha driver profilini topish."""
        result = await db.execute(
            select(Driver)
            .options(joinedload(Driver.user))
            .where(Driver.user_id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all_online(db: AsyncSession) -> list[Driver]:
\
        result = await db.execute(
            select(Driver)
            .options(joinedload(Driver.user))
            .where(Driver.status == DriverStatus.ONLINE)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_online_user_ids(db: AsyncSession) -> list[int]:
        """
        Faqat ONLINE driverlarning user_id'larini olish (tezkor).

        ⭐ Broadcast uchun optimizatsiya:
            Bu yerda User JOIN qilinmaydi (kerak emas) — faqat user_id.
            7000 driver uchun JOIN'siz so'rov ancha tez va kam xotira.

        Returns:
            Online driverlarning user_id ro'yxati
        """
        result = await db.execute(
            select(Driver.user_id).where(Driver.status == DriverStatus.ONLINE)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_all(db: AsyncSession) -> list[Driver]:

        result = await db.execute(
            select(Driver).options(joinedload(Driver.user))
        )
        return list(result.scalars().all())

    @staticmethod
    async def search_by_plate(db: AsyncSession, query: str) -> list[Driver]:

        result = await db.execute(
            select(Driver)
            .options(joinedload(Driver.user))
            .where(Driver.license_plate.ilike(f"%{query}%"))  # ilike = katta/kichik harf farqsiz
        )
        return list(result.scalars().all())

    @staticmethod
    async def update_status(
        db: AsyncSession,
        driver: Driver,
        new_status: DriverStatus,
    ) -> Driver:

        driver.status = new_status
        await db.flush()
        await db.refresh(driver)
        return driver

    @staticmethod
    async def count_online(db: AsyncSession) -> int:
        """Online driverlar sonini hisoblash."""
        result = await db.execute(
            select(func.count(Driver.id))
            .where(Driver.status == DriverStatus.ONLINE)
        )
        return result.scalar_one()


driver_repository = DriverRepository()
