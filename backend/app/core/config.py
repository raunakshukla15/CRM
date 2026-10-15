from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "WooCommerce CRM Backend"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = (
        "mysql+pymysql://crm_user:change_me_strong_password@db:3306/woocommerce_crm"
    )

    WC_WEBHOOK_SECRET: str = "change-me"
    WEBHOOK_SKIP_SIGNATURE: bool = False

    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # --- Auth / server-side sessions ---
    SESSION_COOKIE_NAME: str = "kk_session"
    SESSION_EXPIRE_DAYS: int = 30
    SESSION_INACTIVITY_DAYS: int = 7
    FRONTEND_URL: str = "http://localhost:5173"
    RATE_LIMIT_AUTH_ATTEMPTS: int = 10
    RATE_LIMIT_AUTH_WINDOW_S: int = 600

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "no-reply@example.com"
    SMTP_FROM_NAME: str = "WooCommerce CRM"
    SMTP_USE_TLS: bool = True

    VIP_SPEND_THRESHOLD: float = 500.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
