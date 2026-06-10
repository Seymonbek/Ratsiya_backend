from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
)

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "working",
        "app_name": settings.APP_NAME,
        "debug_mode": settings.DEBUG
    }