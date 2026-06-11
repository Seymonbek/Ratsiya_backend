from app.core.logger import setup_logger
from app.db.base import Base
from app.db.session import engine

logger = setup_logger(__name__)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database jadvallari muvaffaqiyatli yaratildi.")


async def close_db() -> None:
    await engine.dispose()
    logger.info("Database ulanishlari yopildi.")
