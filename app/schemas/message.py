from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    """
    Ovozli xabar yuborilganda operatorga qaytariladigan javob.
    """
    id: int = Field(description="Xabar ID")
    sender_id: int = Field(description="Yuboruvchi (operator) ID")
    sender_name: str = Field(description="Yuboruvchi ismi")
    recipient_id: int | None = Field(
        default=None,
        description="Qabul qiluvchi driver ID (null = broadcast)",
    )
    message_type: str = Field(description="Xabar turi (broadcast/private)")
    audio_url: str = Field(description="Audio'ni olish uchun URL (60s amal qiladi)")
    delivered_to: int = Field(description="Nechta online driverga yetkazildi")
    expires_in: int = Field(description="Necha soniyadan keyin o'chadi")
    created_at: str = Field(description="Yuborilgan vaqt (ISO format)")


class ActiveMessageResponse(BaseModel):
    """
    Aktiv (hali o'chmagan) xabar — Redis'da turgan.

    Faqat 60 soniya ichidagi xabarlar.
    """
    id: int = Field(description="Xabar ID")
    sender_name: str = Field(description="Yuboruvchi ismi")
    message_type: str = Field(description="broadcast yoki private")
    recipient_id: int | None = Field(default=None, description="null = broadcast")
    audio_url: str = Field(description="Audio URL")
    seconds_remaining: int = Field(description="Necha soniya qoldi")
    created_at: str = Field(description="Yuborilgan vaqt")


class ActiveMessageListResponse(BaseModel):
    """Aktiv xabarlar ro'yxati (60s ichida)."""
    messages: list[ActiveMessageResponse] = Field(description="Aktiv xabarlar")
    total: int = Field(description="Aktiv xabarlar soni")


class CachedVoiceMessage(BaseModel):
    """
    Redis'da saqlanadigan xabar META ma'lumoti.
    """
    message_id: int = Field(description="Xabar ID")
    sender_id: int = Field(description="Yuboruvchi ID")
    sender_name: str = Field(description="Yuboruvchi ismi")
    message_type: str = Field(description="broadcast yoki private")
    recipient_id: int | None = Field(default=None, description="null = broadcast")
    content_type: str = Field(description="Audio MIME turi (audio/webm)")
    created_at: str = Field(description="Yuborilgan vaqt (ISO format)")
