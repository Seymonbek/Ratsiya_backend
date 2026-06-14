from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_SECRET_KEYS = {
    "super-secret-key-for-local-development",
    "super-secret-key-change-in-production",
    "changeme",
    "secret",
    "",
}


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


    # Production: "https://frontend.domeningiz.uz"
    CORS_ORIGINS: str = "*"

    VOICE_MESSAGE_TTL: int = 60           # Redis'da 60 soniya (1 daqiqa) saqlanadi
    MAX_VOICE_DURATION_SECONDS: int = 20  # Ovoz maksimal davomiyligi (20 soniya)

    # Rate limiting (brute-force / spam himoyasi)
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_AUTH: str = "10/minute"        # login / register (IP bo'yicha)
    RATE_LIMIT_BROADCAST: str = "30/minute"   # broadcast / private xabar

    # Database connection pool (production tuning)
    DB_POOL_SIZE: int = 20      # Doim tayyor ulanishlar
    DB_MAX_OVERFLOW: int = 30   # Yuklamada qo'shimcha (jami 50)
    DB_POOL_TIMEOUT: int = 30   # Bo'sh ulanish kutish vaqti (soniya)

    @property
    def cors_origins_list(self) -> list[str]:
        """CORS_ORIGINS string'ini ro'yxatga aylantirish."""
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @model_validator(mode="after")
    def _validate_production_security(self) -> "Settings":

        if not self.DEBUG:
            if self.SECRET_KEY.strip() in _INSECURE_SECRET_KEYS:
                raise ValueError(
                    "Production'da (DEBUG=False) xavfli default SECRET_KEY "
                    "ishlatib bo'lmaydi. .env'da kuchli, tasodifiy SECRET_KEY "
                    "o'rnating (masalan: `openssl rand -hex 32`)."
                )
            if len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "Production'da SECRET_KEY kamida 32 belgi bo'lishi kerak. "
                    "Kuchliroq kalit yarating (masalan: `openssl rand -hex 32`)."
                )
        return self


settings = Settings()