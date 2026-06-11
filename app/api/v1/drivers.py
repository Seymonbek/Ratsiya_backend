from fastapi import APIRouter, Depends, Query

from app.dependencies.database import get_db
from app.dependencies.roles import require_operator, require_driver
from app.models.user import User
from app.schemas.driver import (
    DriverResponse,
    DriverStatusUpdate,
    DriverListResponse,
)
from app.services.driver import driver_service
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/drivers", tags=["Drivers"])


def _to_driver_response(driver) -> DriverResponse:
    """Driver modelni DriverResponse'ga aylantirish (full_name bilan)."""
    return DriverResponse(
        id=driver.id,
        user_id=driver.user_id,
        license_plate=driver.license_plate,
        status=driver.status,
        created_at=driver.created_at,
        full_name=driver.user.full_name if driver.user else None,
    )


@router.patch(
    "/me/status",
    response_model=DriverResponse,
    summary="O'z statusini o'zgartirish (Driver)",
)
async def update_my_status(
    data: DriverStatusUpdate,
    current_user: User = Depends(require_driver),
    db: AsyncSession = Depends(get_db),
):

    driver = await driver_service.update_status(
        db=db,
        user_id=current_user.id,
        new_status=data.status,
    )
    return _to_driver_response(driver)


@router.get(
    "/me",
    response_model=DriverResponse,
    summary="O'z profilini ko'rish (Driver)",
)
async def get_my_profile(
    current_user: User = Depends(require_driver),
    db: AsyncSession = Depends(get_db),
):
    """Driver o'z profilini ko'radi (status, mashina raqami)."""
    driver = await driver_service.get_driver_by_user(db, current_user.id)
    return _to_driver_response(driver)


@router.get(
    "",
    response_model=DriverListResponse,
    summary="Barcha driverlar (Operator)",
)
async def get_all_drivers(
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):

    drivers, online_count = await driver_service.get_all_drivers(db)
    return DriverListResponse(
        drivers=[_to_driver_response(d) for d in drivers],
        total=len(drivers),
        online_count=online_count,
    )


@router.get(
    "/online",
    response_model=DriverListResponse,
    summary="Online driverlar (Operator)",
)
async def get_online_drivers(
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):

    drivers = await driver_service.get_online_drivers(db)
    return DriverListResponse(
        drivers=[_to_driver_response(d) for d in drivers],
        total=len(drivers),
        online_count=len(drivers),
    )


@router.get(
    "/search",
    response_model=DriverListResponse,
    summary="Driver qidirish (Operator)",
)
async def search_drivers(
    q: str = Query(..., min_length=1, description="Mashina raqami (qisman)"),
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):

    drivers = await driver_service.search_drivers(db, q)
    return DriverListResponse(
        drivers=[_to_driver_response(d) for d in drivers],
        total=len(drivers),
        online_count=sum(1 for d in drivers if d.status == "online"),
    )
