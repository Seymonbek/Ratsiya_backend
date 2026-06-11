from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

# Bu databasega yo'l ochadi va connection pool boshqaradi
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,          # Doim tayyor ulanishlar
    max_overflow=settings.DB_MAX_OVERFLOW,    # Yuklamada qo'shimcha
    pool_timeout=settings.DB_POOL_TIMEOUT,    # Bo'sh ulanish kutish vaqti
    pool_pre_ping=True,  # Har ishlatishdan oldin ulanish tirikmi tekshiradi
    pool_recycle=1800,   # 30 daqiqada ulanishni yangilash (stale connection oldini olish)
    echo=settings.DEBUG, # True = SQL so'rovlarni console'ga chiqaradi
)

# Har bir request uchun yangi session yaratadi
async_session_factory = async_sessionmaker(
    bind=engine,           # Qaysi engine ishlatsin
    class_=AsyncSession,   # Async session await bilan ishlaydi
    expire_on_commit=False,  # Commitdan keyin obyektlar expired bo'lmasin
)


async def get_async_session() -> AsyncSession:
    async with async_session_factory() as session:
        yield session
