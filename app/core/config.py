from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Ratsiya Backend"
    DEBUG: bool = True

    # Ma'lumotlar bazasi va Redis manzillari (lokal sinov uchun default qiymatlar)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ratsiya_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    VOICE_MESSAGE_TTL: int = 60

    # JWT sozlamalari
    SECRET_KEY: str = "super-secret-key-for-local-development"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 1 kun

settings = Settings()