from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import setup_logger
from app.enums import DriverStatus
from app.models.driver import Driver
from app.repositories.driver import driver_repository

logger = setup_logger(__name__)


class DriverService:
    """Haydovchi servisi."""

    @staticmethod
    async def update_status(
        db: AsyncSession,
        user_id: int,
        new_status: DriverStatus,
    ) -> Driver:

        driver = await driver_repository.get_by_user_id(db, user_id)
        if driver is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Driver profili topilmadi",
            )

        updated = await driver_repository.update_status(db, driver, new_status)
        logger.info(f"Driver {driver.id} status: {new_status}")
        return updated

    @staticmethod
    async def get_driver_by_user(db: AsyncSession, user_id: int) -> Driver:
        """User ID bo'yicha driver profilini olish."""
        driver = await driver_repository.get_by_user_id(db, user_id)
        if driver is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Driver profili topilmadi",
            )
        return driver

    @staticmethod
    async def get_all_drivers(db: AsyncSession) -> tuple[list[Driver], int]:

        drivers = await driver_repository.get_all(db)
        online_count = await driver_repository.count_online(db)
        return drivers, online_count

    @staticmethod
    async def get_online_drivers(db: AsyncSession) -> list[Driver]:

        return await driver_repository.get_all_online(db)

    @staticmethod
    async def search_drivers(db: AsyncSession, query: str) -> list[Driver]:

        return await driver_repository.search_by_plate(db, query)


driver_service = DriverService()
