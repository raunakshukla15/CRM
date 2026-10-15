import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import customers, dashboard, followups, integrations, interactions, orders, webhooks
from app.core.config import get_settings
from app.core.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME, version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["health"])
    def health():
        return {"status": "ok", "env": settings.ENVIRONMENT}

    @app.get("/ready", tags=["health"])
    def ready():
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return {"status": "ready", "db": "up"}
        except Exception as exc:
            logger.exception("Readiness check failed")
            return {"status": "not-ready", "db": "down", "error": str(exc)}

    app.include_router(webhooks.router, prefix=settings.API_V1_PREFIX)
    app.include_router(dashboard.router, prefix=settings.API_V1_PREFIX)
    app.include_router(customers.router, prefix=settings.API_V1_PREFIX)
    app.include_router(orders.router, prefix=settings.API_V1_PREFIX)
    app.include_router(interactions.router, prefix=settings.API_V1_PREFIX)
    app.include_router(followups.router, prefix=settings.API_V1_PREFIX)
    app.include_router(integrations.router, prefix=settings.API_V1_PREFIX)

    @app.on_event("startup")
    def _create_tables_for_development() -> None:
        # Dev convenience: ensure tables exist without running alembic.
        # Production still uses `alembic upgrade head` (see Dockerfile).
        if settings.ENVIRONMENT == "development":
            from app.models import Base  # noqa: F401  (register all models)

            Base.metadata.create_all(bind=engine)
            logger.info("Development auto-create tables: OK")

    return app


app = create_app()
