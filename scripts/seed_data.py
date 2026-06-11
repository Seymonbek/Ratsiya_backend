"""
Test ma'lumotlarini yaratish skripti (seed).

Tizimni tez sinab ko'rish uchun namunaviy ma'lumotlar yaratadi:
    - 1 operator
    - 3 driver (turli statuslar: online, offline, on_trip)

Ishlatilishi:
    python -m scripts.seed_data

Docker'da:
    docker-compose exec app python -m scripts.seed_data
"""

import asyncio

from app.core.security import hash_password
from app.db.session import async_session_factory
from app.enums import UserRole, DriverStatus
from app.repositories.user import user_repository
from app.repositories.driver import driver_repository
from app.models.driver import Driver
from sqlalchemy import select


# Namunaviy ma'lumotlar
OPERATOR = {
    "username": "operator1",
    "password": "operator123",
    "full_name": "Ali Valiyev",
}

DRIVERS = [
    {"username": "driver1", "password": "driver123", "full_name": "Sherali Karimov",
     "license_plate": "90A123PA", "status": DriverStatus.ONLINE},
    {"username": "driver2", "password": "driver123", "full_name": "Olim Toshev",
     "license_plate": "75B456XA", "status": DriverStatus.OFFLINE},
    {"username": "driver3", "password": "driver123", "full_name": "Aziz Rahimov",
     "license_plate": "60C789YA", "status": DriverStatus.ON_TRIP},
]


async def seed() -> None:
    """Namunaviy ma'lumotlarni yaratish."""
    async with async_session_factory() as session:
        # --- Operator ---
        if not await user_repository.exists_by_username(session, OPERATOR["username"]):
            await user_repository.create(
                db=session,
                username=OPERATOR["username"],
                hashed_password=hash_password(OPERATOR["password"]),
                full_name=OPERATOR["full_name"],
                role=UserRole.OPERATOR,
            )
            print(f"✓ Operator: {OPERATOR['username']} / {OPERATOR['password']}")
        else:
            print(f"• Operator '{OPERATOR['username']}' allaqachon mavjud")

        # --- Driverlar ---
        for d in DRIVERS:
            if await user_repository.exists_by_username(session, d["username"]):
                print(f"• Driver '{d['username']}' allaqachon mavjud")
                continue

            # License plate band emasligini tekshirish
            existing_plate = await session.execute(
                select(Driver.id).where(Driver.license_plate == d["license_plate"])
            )
            if existing_plate.scalar_one_or_none() is not None:
                print(f"• Mashina raqami '{d['license_plate']}' allaqachon band — o'tkazib yuborildi")
                continue

            user = await user_repository.create(
                db=session,
                username=d["username"],
                hashed_password=hash_password(d["password"]),
                full_name=d["full_name"],
                role=UserRole.DRIVER,
            )
            driver = await driver_repository.create(
                db=session,
                user_id=user.id,
                license_plate=d["license_plate"],
            )
            # Statusni o'rnatish
            await driver_repository.update_status(session, driver, d["status"])
            print(
                f"✓ Driver: {d['username']} / {d['password']} "
                f"({d['license_plate']}, {d['status']})"
            )

        await session.commit()

    print("\n✓ Seed ma'lumotlari tayyor!")
    print("  Operator: operator1 / operator123")
    print("  Driverlar: driver1, driver2, driver3 / driver123")


if __name__ == "__main__":
    asyncio.run(seed())
