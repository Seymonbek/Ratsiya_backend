import time

from app.core.logger import setup_logger
from app.redis.client import get_redis

logger = setup_logger(__name__)

_BLACKLIST_PREFIX = "jwt_blacklist:"


def _key(jti: str) -> str:
    return f"{_BLACKLIST_PREFIX}{jti}"


async def revoke_token(jti: str, exp: int) -> None:

    ttl = int(exp - time.time())
    if ttl <= 0:
        # Token allaqachon eskirgan — blacklist shart emas
        return

    redis_client = get_redis()
    await redis_client.set(_key(jti), "1", ex=ttl)
    logger.info(f"Token bekor qilindi: jti={jti} (TTL={ttl}s)")


async def is_revoked(jti: str) -> bool:
    """Token bekor qilinganmi (blacklist'da bormi)."""
    if not jti:
        return False
    redis_client = get_redis()
    return await redis_client.exists(_key(jti)) > 0
