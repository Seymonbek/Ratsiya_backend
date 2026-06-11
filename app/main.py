from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logger import setup_logger
from app.api.v1.router import api_router
from app.db.init_db import init_db, close_db
from app.redis.client import RedisClient
from app.redis.pubsub import start_subscriber, stop_subscriber

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):

    # STARTUP
    logger.info("Server ishga tushmoqda...")

    # Database
    await init_db()

    # Redis
    await RedisClient.connect()

    # Pub/Sub subscriber (bir nechta server uchun real-time)
    await start_subscriber()

    logger.info(f"{settings.APP_NAME} tayyor ✓")

    yield  # ← Bu yerda ilova ishlaydi

    # SHUTDOWN
    logger.info("Server to'xtamoqda...")
    await stop_subscriber()
    await RedisClient.disconnect()
    await close_db()
    logger.info("Server to'xtatildi.")


# FastAPI ilovasi
app = FastAPI(
    title=settings.APP_NAME,
    description="Real-Time Ratsiya (Dispatcher ↔ Driver) — Ovozli xabar tizimi",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",      # Swagger UI manzili
    redoc_url="/redoc",    # ReDoc manzili
)


# Frontend (boshqa domendan) ulana olishi uchun
# Production'da CORS_ORIGINS env orqali aniq domenга cheklanadi
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],       # GET, POST, PATCH
    allow_headers=["*"],       # Barcha headerlar
)

# API routerlar
app.include_router(api_router)


# Health check — server, DB va Redis holatini tekshiradi
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Server holatini tekshirish (monitoring / load balancer uchun).

    DB va Redis ulanishini ham tekshiradi.
    Biror servis ishlamasa — status "degraded".
    """
    from sqlalchemy import text
    from app.db.session import engine
    from app.redis.client import get_redis

    db_ok = False
    redis_ok = False

    # DB tekshirish
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        logger.error(f"Health: DB xatosi: {e}")

    # Redis tekshirish
    try:
        await get_redis().ping()
        redis_ok = True
    except Exception as e:
        logger.error(f"Health: Redis xatosi: {e}")

    all_ok = db_ok and redis_ok
    return {
        "status": "ok" if all_ok else "degraded",
        "app_name": settings.APP_NAME,
        "version": "1.0.0",
        "services": {
            "database": "ok" if db_ok else "down",
            "redis": "ok" if redis_ok else "down",
        },
    }


@app.get("/", tags=["Health"])
async def root():
    """Asosiy sahifa — dokumentatsiyaga yo'naltiradi."""
    return {
        "message": "Ratsiya Backend API",
        "docs": "/docs",
        "health": "/health",
    }
