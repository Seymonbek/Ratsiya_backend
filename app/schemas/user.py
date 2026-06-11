from datetime import datetime

from pydantic import BaseModel, Field

from app.enums import UserRole


class UserResponse(BaseModel):

    id: int = Field(description="Foydalanuvchi ID")
    username: str = Field(description="Login nomi")
    full_name: str = Field(description="To'liq ism")
    role: UserRole = Field(description="Rol (operator/driver)")
    is_active: bool = Field(description="Faol holati")
    created_at: datetime = Field(description="Ro'yxatdan o'tgan vaqti")

    model_config = {"from_attributes": True}