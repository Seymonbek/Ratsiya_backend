import io

from fastapi import HTTPException, UploadFile, status
from mutagen import File as MutagenFile

from app.core.config import settings
from app.core.constants import MAX_VOICE_FILE_SIZE, ALLOWED_AUDIO_TYPES


def validate_audio_file(file: UploadFile) -> None:
    """Audio fayl TURINI tekshirish."""
    if file.content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Noto'g'ri fayl turi: {file.content_type}. "
                f"Ruxsat etilgan: {', '.join(ALLOWED_AUDIO_TYPES)}"
            ),
        )


def validate_audio_size(audio_bytes: bytes) -> None:
    """Audio HAJMINI tekshirish (tezkor himoya, davomiylikdan oldin)."""
    if len(audio_bytes) > MAX_VOICE_FILE_SIZE:
        max_mb = MAX_VOICE_FILE_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=413,  # Content Too Large
            detail=(
                f"Audio juda katta ({len(audio_bytes) / (1024*1024):.1f} MB). "
                f"Maksimal: {max_mb:.0f} MB."
            ),
        )


def validate_audio_duration(audio_bytes: bytes) -> None:

    max_duration = settings.MAX_VOICE_DURATION_SECONDS

    try:
        audio = MutagenFile(io.BytesIO(audio_bytes))
    except Exception:
        audio = None

    # Davomiylikni o'qishga harakat
    if audio is not None and getattr(audio, "info", None) is not None:
        duration = getattr(audio.info, "length", None)
        if duration is not None and duration > max_duration:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Ovoz juda uzun ({duration:.1f} soniya). "
                    f"Maksimal: {max_duration} soniya."
                ),
            )
