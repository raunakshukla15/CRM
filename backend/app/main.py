import logging
from urllib.parse import urlparse

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api import (
    activity,
    auth,
    customers,
    dashboard,
    followups,
    interactions,
    orders,
    webhooks,
)
from app.core.config import get_settings
from app.core.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


def _allowed_origin_hosts() -> set[str]:
    hosts: set[str] = set()
    for origin in settings.BACKEND_CORS_ORIGINS:
        try:
            hosts.add(urlparse(origin).hostname or "")
        except Exception:
            continue
    return {h for h in hosts if h}


def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME, version="2.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def csrf_origin_check(request: Request, call_next):
        # Cookie-based auth CSRF defence: state-changing requests carrying a
        # browser Origin must come from an allowed frontend origin. API clients
        # and tools without an Origin header (curl, tests, webhooks) pass through.
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            origin = request.headers.get("origin")
            if origin:
                host = (urlparse(origin).hostname or "").lower()
                allowed = {h.lower() for h in _allowed_origin_hosts()}
                if host not in allowed:
                    return JSONResponse(
                        status_code=403, content={"detail": "CSRF check failed: bad origin."}
                    )
        return await call_next(request)

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

    app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
    app.include_router(activity.router, prefix=settings.API_V1_PREFIX)
    app.include_router(webhooks.router, prefix=settings.API_V1_PREFIX)
    app.include_router(dashboard.router, prefix=settings.API_V1_PREFIX)
    app.include_router(customers.router, prefix=settings.API_V1_PREFIX)
    app.include_router(orders.router, prefix=settings.API_V1_PREFIX)
    app.include_router(interactions.router, prefix=settings.API_V1_PREFIX)
    app.include_router(followups.router, prefix=settings.API_V1_PREFIX)

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
