"""Auth dependencies: resolve the session cookie against MySQL on every request."""

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session as DBSession

from app.core.config import get_settings
from app.core.database import get_db
from app.models.user import Session as SessionRow, User
from app.services.auth import resolve_session


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    return (request.client.host if request.client else "unknown")[:64]


async def get_current_user(
    request: Request, db: DBSession = Depends(get_db)
) -> User:
    """Authenticated identity comes ONLY from the session cookie → MySQL lookup.

    Never trust a user ID supplied by the frontend.
    """
    settings = get_settings()
    raw = request.cookies.get(settings.SESSION_COOKIE_NAME)
    user, _ = resolve_session(db, raw)
    db.commit()  # persist last_activity_at / inactivity revocation
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    return user


async def get_current_session(
    request: Request, db: DBSession = Depends(get_db)
) -> tuple[User, SessionRow]:
    settings = get_settings()
    raw = request.cookies.get(settings.SESSION_COOKIE_NAME)
    user, session = resolve_session(db, raw)
    db.commit()
    if user is None or session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    return user, session
