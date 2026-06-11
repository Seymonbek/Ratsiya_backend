MAX_VOICE_FILE_SIZE: int = 3 * 1024 * 1024  # 3 MB (baytlarda)

ALLOWED_AUDIO_TYPES: list[str] = [
    "audio/webm",   # Brauzerdan yozilgan ovoz
    "audio/ogg",    # Ogg format
    "audio/mpeg",   # MP3
    "audio/wav",    # WAV
]

# --- WebSocket ---
WS_HEARTBEAT_INTERVAL: int = 30  # Har 30 soniyada "tirikman" signal

# --- Xabar turlari ---
MESSAGE_TYPE_BROADCAST: str = "broadcast"  # Barcha online driverlarga
MESSAGE_TYPE_PRIVATE: str = "private"      # Faqat bitta driverga

# --- Redis kalitlari ---
# Ovoz endi DISKKA emas, Redis'ga saqlanadi (60s, keyin o'chadi).
VOICE_CACHE_PREFIX: str = "voice_msg:"      # voice_msg:{id} → meta + audio
VOICE_AUDIO_PREFIX: str = "voice_audio:"    # voice_audio:{id} → audio bytes (base64)
VOICE_ID_COUNTER: str = "voice_msg:counter"  # xabar ID generatori (atomik)
