from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Asosiy sozlamalar klassi.
    Pydantic-settings .env fayldagi qiymatlarni avtomatik o'qiydi.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    APP_NAME: str = "Ratsiya Backend"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/ratsiya_db"

    REDIS_URL: str = "redis://redis:6379/0"

    SECRET_KEY: str = "super-secret-key-for-local-development"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # --- CORS (frontend ulanishi) ---
    # Vergul bilan ajratilgan domenlar yoki "*" (hamma).
    # Production: "https://frontend.domeningiz.uz"
    CORS_ORIGINS: str = "*"

    VOICE_MESSAGE_TTL: int = 60           # Redis'da 60 soniya (1 daqiqa) saqlanadi
    MAX_VOICE_DURATION_SECONDS: int = 20  # Ovoz maksimal davomiyligi (20 soniya)

    # --- Database connection pool (production tuning) ---
    DB_POOL_SIZE: int = 20      # Doim tayyor ulanishlar
    DB_MAX_OVERFLOW: int = 30   # Yuklamada qo'shimcha (jami 50)
    DB_POOL_TIMEOUT: int = 30   # Bo'sh ulanish kutish vaqti (soniya)

    @property
    def cors_origins_list(self) -> list[str]:
        """CORS_ORIGINS string'ini ro'yxatga aylantirish."""
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()