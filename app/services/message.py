from datetime import datetime, timezone

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import setup_logger
from app.core.constants import MESSAGE_TYPE_BROADCAST, MESSAGE_TYPE_PRIVATE
from app.enums import DriverStatus, UserRole
from app.models.user import User
from app.repositories.driver import driver_repository
from app.services.storage import storage_service
from app.redis.cache import generate_message_id, store_voice_message
from app.schemas.message import CachedVoiceMessage

logger = setup_logger(__name__)


class MessageService:
    """Ovozli xabar servisi (Redis-based, DB'siz)."""

    @staticmethod
    async def can_user_access(
        db: AsyncSession,
        user: User,
        meta: CachedVoiceMessage,
    ) -> bool:

        # 1. Broadcast — hammaga ochiq
        if meta.message_type == MESSAGE_TYPE_BROADCAST:
            return True

        # 2. Yuboruvchining o'zi (operator)
        if meta.sender_id == user.id:
            return True

        # 3. Private — faqat qabul qiluvchi driver
        if user.role == UserRole.DRIVER:
            driver = await driver_repository.get_by_user_id(db, user.id)
            if driver is not None and driver.id == meta.recipient_id:
                return True

        return False

    @staticmethod
    async def send_broadcast(
        db: AsyncSession,
        sender: User,
        file: UploadFile,
    ) -> tuple[CachedVoiceMessage, list[int]]:

        # 1. Audio o'qish + tekshirish
        audio_bytes, content_type = await storage_service.read_and_validate(file)

        # 2. Xabar ID (Redis counter)
        message_id = await generate_message_id()

        # 3. Meta yaratish
        meta = CachedVoiceMessage(
            message_id=message_id,
            sender_id=sender.id,
            sender_name=sender.full_name,
            message_type=MESSAGE_TYPE_BROADCAST,
            recipient_id=None,
            content_type=content_type,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        # 4. Redis'ga saqlash (audio + meta, 60s)
        await store_voice_message(meta, audio_bytes)

        # 5. Online driverlarni topish (faqat user_id — tezkor, JOIN'siz)
        online_user_ids = await driver_repository.get_online_user_ids(db)

        logger.info(
            f"Broadcast: operator={sender.username}, "
            f"online={len(online_user_ids)}, msg_id={message_id}"
        )
        return meta, online_user_ids

    @staticmethod
    async def send_private(
        db: AsyncSession,
        sender: User,
        file: UploadFile,
        driver_id: int,
    ) -> tuple[CachedVoiceMessage, int]:

        # 1. Driverni topish
        driver = await driver_repository.get_by_id(db, driver_id)
        if driver is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Driver topilmadi",
            )

        # 2. ONLINE tekshirish (TZ qoidasi)
        if driver.status != DriverStatus.ONLINE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Driver '{driver.license_plate}' hozir {driver.status}. "
                    f"Faqat online driverlarga xabar yuborish mumkin."
                ),
            )

        # 3. Audio o'qish + tekshirish
        audio_bytes, content_type = await storage_service.read_and_validate(file)

        # 4. Xabar ID
        message_id = await generate_message_id()

        # 5. Meta
        meta = CachedVoiceMessage(
            message_id=message_id,
            sender_id=sender.id,
            sender_name=sender.full_name,
            message_type=MESSAGE_TYPE_PRIVATE,
            recipient_id=driver_id,
            content_type=content_type,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        # 6. Redis'ga saqlash (60s)
        await store_voice_message(meta, audio_bytes)

        logger.info(
            f"Private: operator={sender.username} → "
            f"driver={driver.license_plate}, msg_id={message_id}"
        )
        return meta, driver.user_id


message_service = MessageService()
