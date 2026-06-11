from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.drivers import router as drivers_router
from app.api.v1.messages import router as messages_router
from app.api.v1.ws import router as ws_router

# v1 asosiy router
api_router = APIRouter(prefix="/api/v1")

# Barcha sub-routerlarni ulash
api_router.include_router(auth_router)
api_router.include_router(drivers_router)
api_router.include_router(messages_router)
api_router.include_router(ws_router)
