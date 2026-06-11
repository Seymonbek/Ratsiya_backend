from fastapi import UploadFile

from app.core.logger import setup_logger
from app.utils.validators import (
    validate_audio_file,
    validate_audio_content,
    validate_audio_size,
    validate_audio_duration,
)

logger = setup_logger(__name__)


class StorageService:

    @staticmethod
    async def read_and_validate(file: UploadFile) -> tuple[bytes, str]:
        
        # 1. Fayl turini tekshirish (Content-Type)
        validate_audio_file(file)

        # 2. Baytlarni o'qish
        audio_bytes = await file.read()

        # 3. Magic bytes — haqiqatan audio'mi (soxta Content-Type himoyasi)
        validate_audio_content(audio_bytes)

        # 4. Hajmni tekshirish
        validate_audio_size(audio_bytes)

        # 5. Davomiylikni aniq tekshirish (max 20s, buzilgan → rad)
        validate_audio_duration(audio_bytes)

        content_type = file.content_type or "audio/webm"
        logger.info(f"Audio qabul qilindi: {len(audio_bytes)} bayt, {content_type}")
        return audio_bytes, content_type


storage_service = StorageService()
