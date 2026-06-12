from app.core.constants import PRESENCE_PREFIX, PRESENCE_TTL
from app.core.logger import setup_logger
from app.redis.client import get_redis

logger = setup_logger(__name__)


def _key(user_id: int) -> str:
    return f"{PRESENCE_PREFIX}{user_id}"


async def mark_online(user_id: int) -> None:
    """Driver'ni online deb belgilash / TTL'ni yangilash (heartbeat)."""
    redis_client = get_redis()
    await redis_client.set(_key(user_id), "1", ex=PRESENCE_TTL)


async def mark_offline(user_id: int) -> None:
    """Driver presence kalitini o'chirish (uzilganda)."""
    redis_client = get_redis()
    await redis_client.delete(_key(user_id))


async def is_online(user_id: int) -> bool:
    """Driver hozir haqiqatan online (presence kaliti bormi)."""
    redis_client = get_redis()
    return await redis_client.exists(_key(user_id)) > 0


async def filter_online(user_ids: list[int]) -> list[int]:

    if not user_ids:
        return []

    redis_client = get_redis()
    pipe = redis_client.pipeline()
    for uid in user_ids:
        pipe.exists(_key(uid))
    results = await pipe.execute()

    return [uid for uid, exists in zip(user_ids, results) if exists]
