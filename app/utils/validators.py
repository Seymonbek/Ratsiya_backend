import io

from fastapi import HTTPException, UploadFile, status
from mutagen import File as MutagenFile

from app.core.config import settings
from app.core.constants import MAX_VOICE_FILE_SIZE, ALLOWED_AUDIO_TYPES


def _looks_like_audio(audio_bytes: bytes) -> bool:
    """Fayl boshini tekshirish — haqiqatan audio formatmi."""
    if len(audio_bytes) < 4:
        return False

    head = audio_bytes[:12]

    # WebM / Matroska: EBML header (0x1A45DFA3)
    if head[:4] == b"\x1a\x45\xdf\xa3":
        return True
    # OGG: "OggS"
    if head[:4] == b"OggS":
        return True
    # WAV: "RIFF"...."WAVE"
    if head[:4] == b"RIFF" and head[8:12] == b"WAVE":
        return True
    # MP3: "ID3" tag yoki frame sync (0xFFEx/0xFFFx)
    if head[:3] == b"ID3":
        return True
    if head[0] == 0xFF and (head[1] & 0xE0) == 0xE0:
        return True

    return False


def validate_audio_file(file: UploadFile) -> None:
    """Audio fayl Content-Type'ini tekshirish (tezkor, birinchi qatlam)."""
    if file.content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Noto'g'ri fayl turi: {file.content_type}. "
                f"Ruxsat etilgan: {', '.join(ALLOWED_AUDIO_TYPES)}"
            ),
        )


def validate_audio_content(audio_bytes: bytes) -> None:

    if not _looks_like_audio(audio_bytes):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fayl haqiqiy audio formatda emas (buzilgan yoki soxta).",
        )


def validate_audio_size(audio_bytes: bytes) -> None:
    """Audio HAJMINI tekshirish."""
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

    # Davomiylik aniqlanmasa — RAD etish (oldin o'tkazib yuborardi)
    if audio is None or getattr(audio, "info", None) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio davomiyligini aniqlab bo'lmadi (buzilgan format).",
        )

    duration = getattr(audio.info, "length", None)
    if duration is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio davomiyligini aniqlab bo'lmadi.",
        )

    if duration > max_duration:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Ovoz juda uzun ({duration:.1f} soniya). "
                f"Maksimal: {max_duration} soniya."
            ),
        )
