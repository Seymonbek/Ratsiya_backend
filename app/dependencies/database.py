from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:

    async with async_session_factory() as session:
        try:
            yield session
            # Request muvaffaqiyatli tugasa — commit saqlash
            await session.commit()
        except Exception:
            # Xato bo'lsa — rollback bekor qilish
            await session.rollback()
            raise
