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

    # --- WooCommerce REST API (server-side only — never exposed to frontend) ---
    WC_STORE_URL: str = ""
    WC_CONSUMER_KEY: str = ""
    WC_CONSUMER_SECRET: str = ""

    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

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
