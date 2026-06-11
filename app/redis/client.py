import redis.asyncio as redis

from app.core.config import settings
from app.core.logger import setup_logger

logger = setup_logger(__name__)


class RedisClient:

    _client: redis.Redis | None = None

    @classmethod
    async def connect(cls) -> None:

        cls._client = redis.from_url(
            settings.REDIS_URL,
            max_connections=50,       # Connection pool hajmi
            decode_responses=True,    # bytes → str avtomatik (qulay)
            socket_keepalive=True,    # Ulanishni tirik saqlash
        )
        # Ulanishni tekshirish (ping)
        await cls._client.ping()
        logger.info("Redis'ga muvaffaqiyatli ulandi.")

    @classmethod
    async def disconnect(cls) -> None:
        """Redis ulanishni yopish (server to'xtaganda)."""
        if cls._client is not None:
            await cls._client.aclose()
            logger.info("Redis ulanishi yopildi.")

    @classmethod
    def get_client(cls) -> redis.Redis:

        if cls._client is None:
            raise RuntimeError(
                "Redis ulanmagan! Avval RedisClient.connect() chaqiring."
            )
        return cls._client


# Qulay funksiya
def get_redis() -> redis.Redis:
    """Redis client olish (qisqa yo'l)."""
    return RedisClient.get_client()
