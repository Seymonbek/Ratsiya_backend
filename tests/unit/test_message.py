import io
import wave

import pytest
from fastapi import HTTPException

from app.core.constants import (
    MESSAGE_TYPE_BROADCAST,
    MESSAGE_TYPE_PRIVATE,
    MAX_VOICE_FILE_SIZE,
)
from app.utils.validators import (
    validate_audio_size,
    validate_audio_duration,
    validate_audio_content,
)


def _make_wav(seconds: int) -> bytes:
    """Test uchun berilgan soniyalik WAV yaratish."""
    buf = io.BytesIO()
    rate = 8000
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(1)
        w.setframerate(rate)
        w.writeframes(b"\x80" * (rate * seconds))
    return buf.getvalue()


class TestMessageConstants:
    """Xabar turi konstantalari."""

    def test_message_types(self):
        assert MESSAGE_TYPE_BROADCAST == "broadcast"
        assert MESSAGE_TYPE_PRIVATE == "private"


class TestAudioSizeValidation:
    """Audio hajm validatsiyasi (20s ~ <3MB)."""

    def test_small_audio_passes(self):
        """Kichik audio o'tishi kerak."""
        small_audio = b"x" * 1024  # 1 KB
        validate_audio_size(small_audio)  # xato bermasligi kerak

    def test_large_audio_rejected(self):
        """Katta audio rad etilishi kerak (413)."""
        large_audio = b"x" * (MAX_VOICE_FILE_SIZE + 1)
        with pytest.raises(HTTPException) as exc:
            validate_audio_size(large_audio)
        assert exc.value.status_code == 413

    def test_exact_limit_passes(self):
        """Aniq limitdagi audio o'tishi kerak."""
        exact = b"x" * MAX_VOICE_FILE_SIZE
        validate_audio_size(exact)  # xato bermasligi kerak


class TestAudioDurationValidation:
    """Audio davomiylik validatsiyasi (max 20 soniya)."""

    def test_short_audio_passes(self):
        """10 soniyalik ovoz o'tishi kerak."""
        validate_audio_duration(_make_wav(10))  # xato bermasligi kerak

    def test_exactly_20s_passes(self):
        """Aniq 20 soniya o'tishi kerak (limit chegarasi)."""
        validate_audio_duration(_make_wav(20))

    def test_long_audio_rejected(self):
        """25 soniyalik ovoz rad etilishi kerak (400)."""
        with pytest.raises(HTTPException) as exc:
            validate_audio_duration(_make_wav(25))
        assert exc.value.status_code == 400

    def test_unparseable_audio_rejected(self):
        """Davomiylik aniqlanmasa (buzilgan/soxta) — RAD etiladi (bypass himoyasi)."""
        with pytest.raises(HTTPException) as exc:
            validate_audio_duration(b"not a real audio file")
        assert exc.value.status_code == 400


class TestAudioContentValidation:
    """Magic bytes validatsiyasi (soxta Content-Type himoyasi)."""

    def test_real_wav_passes(self):
        """Haqiqiy WAV magic bytes tekshiruvidan o'tadi."""
        validate_audio_content(_make_wav(5))

    def test_fake_audio_rejected(self):
        """Soxta fayl (audio emas) rad etiladi (400)."""
        with pytest.raises(HTTPException) as exc:
            validate_audio_content(b"this is not audio, maybe an exe or png")
        assert exc.value.status_code == 400

    def test_png_disguised_as_audio_rejected(self):
        """PNG (rasm) audio sifatida yuborilsa — rad etiladi."""
        png_header = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20
        with pytest.raises(HTTPException) as exc:
            validate_audio_content(png_header)
        assert exc.value.status_code == 400
