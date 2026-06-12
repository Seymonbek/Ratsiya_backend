import base64
import json

from app.core.config import settings
from app.core.constants import (
    VOICE_CACHE_PREFIX,
    VOICE_AUDIO_PREFIX,
    VOICE_ID_COUNTER,
)
from app.core.logger import setup_logger
from app.redis.client import get_redis
from app.schemas.message import CachedVoiceMessage

logger = setup_logger(__name__)


def _meta_key(message_id: int) -> str:
    """Meta kalit: voice_msg:123"""
    return f"{VOICE_CACHE_PREFIX}{message_id}"


def _audio_key(message_id: int) -> str:
    """Audio kalit: voice_audio:123"""
    return f"{VOICE_AUDIO_PREFIX}{message_id}"


async def generate_message_id() -> int:

    redis_client = get_redis()
    return await redis_client.incr(VOICE_ID_COUNTER)


async def store_voice_message(
    meta: CachedVoiceMessage,
    audio_bytes: bytes,
) -> None:

    redis_client = get_redis()
    ttl = settings.VOICE_MESSAGE_TTL

    # Audio'ni base64'ga aylantirish (binary → matn)
    audio_b64 = base64.b64encode(audio_bytes).decode("ascii")

    # Pipeline — ikkala yozuvni bitta so'rovda (tezroq, atomik)
    pipe = redis_client.pipeline()
    pipe.set(_meta_key(meta.message_id), meta.model_dump_json(), ex=ttl)
    pipe.set(_audio_key(meta.message_id), audio_b64, ex=ttl)
    await pipe.execute()

    logger.debug(f"Ovoz Redis'ga saqlandi: id={meta.message_id} (TTL={ttl}s)")


async def get_voice_meta(message_id: int) -> CachedVoiceMessage | None:

    redis_client = get_redis()
    value = await redis_client.get(_meta_key(message_id))
    if value is None:
        return None
    return CachedVoiceMessage(**json.loads(value))


async def get_voice_audio(message_id: int) -> bytes | None:

    redis_client = get_redis()
    audio_b64 = await redis_client.get(_audio_key(message_id))
    if audio_b64 is None:
        return None
    return base64.b64decode(audio_b64)


async def get_voice_ttl(message_id: int) -> int:

    redis_client = get_redis()
    return await redis_client.ttl(_meta_key(message_id))


async def list_active_messages() -> list[tuple[CachedVoiceMessage, int]]:

    redis_client = get_redis()

    # 1. Barcha voice_msg:* kalitlarni yig'ish (counter'dan tashqari)
    keys: list[str] = []
    async for key in redis_client.scan_iter(match=f"{VOICE_CACHE_PREFIX}*"):
        if key == VOICE_ID_COUNTER:
            continue
        keys.append(key)

    if not keys:
        return []

    # 2. Barcha meta + TTL'ni bitta pipeline'da olish
    pipe = redis_client.pipeline()
    for key in keys:
        pipe.get(key)
        pipe.ttl(key)
    results = await pipe.execute()

    # 3. Natijalarni yig'ish (results: [meta0, ttl0, meta1, ttl1, ...])
    items: list[tuple[CachedVoiceMessage, int]] = []
    for i in range(0, len(results), 2):
        value = results[i]
        ttl = results[i + 1]
        if not value or ttl is None or ttl <= 0:
            continue
        try:
            meta = CachedVoiceMessage(**json.loads(value))
        except (json.JSONDecodeError, ValueError):
            continue
        items.append((meta, ttl))

    # Yangi → eski tartibda
    items.sort(key=lambda pair: pair[0].message_id, reverse=True)
    return items
