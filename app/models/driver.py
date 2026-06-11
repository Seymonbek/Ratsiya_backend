from sqlalchemy import String, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.enums import DriverStatus


class Driver(Base):
    __tablename__ = "drivers"

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    license_plate: Mapped[str] = mapped_column(
        String(20),       # Mashina raqami: "90A123PA"
        unique=True,
        nullable=False,
        index=True,       # Raqam bo'yicha qidirish (rasmda SEARCH bor)
    )

    status: Mapped[str] = mapped_column(
        String(20),       # "online", "offline", "on_trip"
        default=DriverStatus.OFFLINE,          # Yangi driver boshlang'ichda offline
        server_default=DriverStatus.OFFLINE,   # DB darajasida ham
        nullable=False,
        index=True,       # Barcha online driverlar so'rovi tez bo'lishi uchun
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="driver_profile",  # User modelidagi field nomi
    )

    def __repr__(self) -> str:
        return (
            f"<Driver(id={self.id}, plate='{self.license_plate}', "
            f"status='{self.status}')>"
        )

    @property
    def is_online(self) -> bool:
        return self.status == DriverStatus.ONLINE
