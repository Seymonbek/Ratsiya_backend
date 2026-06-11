from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.enums import UserRole


class User(Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(50),       # Maksimal 50 ta belgi
        unique=True,      # Takrorlanmas login ikkinchi marta bo'lmaydi
        index=True,       # Tez qidirish uchun login paytida
        nullable=False,   # Bo'sh bo'lishi mumkin emas
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    full_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(20),       # "operator" yoki "driver"
        nullable=False,
        index=True,       # Rolga qarab filtr qilish tez bo'ladi
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,     # Yangi user avtomatik aktiv
        server_default="true",
    )

    driver_profile: Mapped["Driver"] = relationship(
        "Driver",
        back_populates="user",     # Driver modelida ham "user" field bor
        uselist=False,             # 1:1 bog'lanish list emas, bitta obyekt
        cascade="all, delete-orphan",  # User o'chirilsa, driver profili ham o'chadi
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
