from datetime import datetime

from pydantic import BaseModel, Field

from app.enums import DriverStatus


class DriverResponse(BaseModel):

    id: int = Field(description="Driver profil ID")
    user_id: int = Field(description="Bog'langan User ID")
    license_plate: str = Field(description="Mashina raqami")
    status: DriverStatus = Field(description="Holati (online/offline/on_trip)")
    created_at: datetime = Field(description="Yaratilgan vaqti")

    # User ma'lumotlari (qo'shimcha)
    full_name: str | None = Field(default=None, description="Haydovchi ismi")

    model_config = {"from_attributes": True}


class DriverStatusUpdate(BaseModel):

    status: DriverStatus = Field(
        description="Yangi status (online/offline/on_trip)",
        examples=["online"],
    )


class DriverListResponse(BaseModel):

    drivers: list[DriverResponse] = Field(description="Driverlar ro'yxati")
    total: int = Field(description="Jami driverlar soni")
    online_count: int = Field(description="Hozir online driverlar soni")
