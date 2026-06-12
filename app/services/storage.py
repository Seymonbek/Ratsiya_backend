from fastapi import HTTPException, UploadFile, status

from app.core.logger import setup_logger
from app.core.constants import MAX_VOICE_FILE_SIZE
from app.utils.validators import (
    validate_audio_file,
    validate_audio_content,
    validate_audio_size,
    validate_audio_duration,
)

logger = setup_logger(__name__)

# Chunk hajmi (o'qishni bo'lak-bo'lak qilish uchun)
_READ_CHUNK_SIZE = 64 * 1024  # 64 KB


def _too_large_error(size_bytes: int | None = None) -> HTTPException:
    max_mb = MAX_VOICE_FILE_SIZE / (1024 * 1024)
    if size_bytes is not None:
        detail = (
            f"Audio juda katta ({size_bytes / (1024 * 1024):.1f} MB). "
            f"Maksimal: {max_mb:.0f} MB."
        )
    else:
        detail = f"Audio juda katta. Maksimal: {max_mb:.0f} MB."
    return HTTPException(status_code=413, detail=detail)


class StorageService:

    @staticmethod
    async def _read_with_limit(file: UploadFile) -> bytes:

        # 1. Content-Length bo'yicha tezkor rad (mavjud bo'lsa)
        if file.size is not None and file.size > MAX_VOICE_FILE_SIZE:
            raise _too_large_error(file.size)

        # 2. Chunk'lab o'qish + early-abort
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = await file.read(_READ_CHUNK_SIZE)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_VOICE_FILE_SIZE:
                raise _too_large_error(total)
            chunks.append(chunk)

        return b"".join(chunks)

    @staticmethod
    async def read_and_validate(file: UploadFile) -> tuple[bytes, str]:

        # 1. Fayl turini tekshirish (Content-Type)
        validate_audio_file(file)

        # 2. Baytlarni xavfsiz o'qish (limitdan oshsa darhol to'xtaydi)
        audio_bytes = await StorageService._read_with_limit(file)

        # 3. Magic bytes — haqiqatan audio'mi (soxta Content-Type himoyasi)
        validate_audio_content(audio_bytes)

        # 4. Hajmni tekshirish (ikkinchi qatlam — to'liq aniqlik uchun)
        validate_audio_size(audio_bytes)

        # 5. Davomiylikni aniq tekshirish (max 20s, buzilgan → rad)
        validate_audio_duration(audio_bytes)

        content_type = file.content_type or "audio/webm"
        logger.info(f"Audio qabul qilindi: {len(audio_bytes)} bayt, {content_type}")
        return audio_bytes, content_type


storage_service = StorageService()
