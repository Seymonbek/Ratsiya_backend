MAX_VOICE_FILE_SIZE: int = 3 * 1024 * 1024  # 3 MB (baytlarda)

ALLOWED_AUDIO_TYPES: list[str] = [
    "audio/webm",   # Brauzerdan yozilgan ovoz
    "audio/ogg",    # Ogg format
    "audio/mpeg",   # MP3
    "audio/wav",    # WAV
]

WS_HEARTBEAT_INTERVAL: int = 30  # Client har 30 soniyada "tirikman" (ping) yuboradi

# Server shu vaqt ichida client'dan hech narsa kelmasa — ulanish o'lik deb
# hisoblanadi va yopiladi (yarim ochiq ulanishlarni tozalash).
# Heartbeat'dan kattaroq: client 30s da ping yuborsa, ulanish tirik qoladi.
WS_RECEIVE_TIMEOUT: int = 60

# Ping kelganda TTL yangilanadi. Server qulasa — TTL tugab kalit o'zi o'chadi.
PRESENCE_PREFIX: str = "online:driver:"
PRESENCE_TTL: int = 75  # WS_RECEIVE_TIMEOUT'dan kattaroq (flapping bo'lmasligi uchun)

# Xabar turlari
MESSAGE_TYPE_BROADCAST: str = "broadcast"  # Barcha online driverlarga
MESSAGE_TYPE_PRIVATE: str = "private"      # Faqat bitta driverga

# Ovoz Redis'ga saqlanadi (60s, keyin o'chadi).
VOICE_CACHE_PREFIX: str = "voice_msg:"      # voice_msg:{id} → meta + audio
VOICE_AUDIO_PREFIX: str = "voice_audio:"    # voice_audio:{id} → audio bytes (base64)
VOICE_ID_COUNTER: str = "voice_msg:counter"  # xabar ID generatori (atomik)
