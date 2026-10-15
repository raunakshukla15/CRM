"""Password hashing (bcrypt) + server-side session management.

Sessions: cryptographically secure random token; only SHA-256 hash stored in
MySQL; raw token travels in an HTTP-only cookie. Expiry + inactivity timeout
enforced on every protected request.
"""

import hashlib
import secrets
from datetime import datetime, timedelta

import bcrypt
from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.core.config import get_settings
from app.models.user import Session as SessionRow, User


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def validate_password_strength(password: str) -> str | None:
    """Return an error message if the password is too weak, else None."""
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if len(password) > 128:
        return "Password must be at most 128 characters long."
    has_letter = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)
    if not (has_letter and has_digit):
        return "Password must contain at least one letter and one number."
    return None


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_session(
    db: DBSession, user: User, ip: str | None = None, user_agent: str | None = None
) -> str:
    """Create a session row and return the RAW token (set as cookie)."""
    settings = get_settings()
    now = datetime.utcnow()
    raw = secrets.token_urlsafe(48)
    row = SessionRow(
        token_hash=_hash_token(raw),
        user_id=user.id,
        created_at=now,
        last_activity_at=now,
        expires_at=now + timedelta(days=settings.SESSION_EXPIRE_DAYS),
        ip_address=(ip or "")[:64] or None,
        user_agent=(user_agent or "")[:500] or None,
    )
    db.add(row)
    db.flush()
    return raw


def resolve_session(db: DBSession, raw_token: str | None) -> tuple[User | None, SessionRow | None]:
    """Validate cookie token against MySQL. Returns (user, session) or (None, None)."""
    if not raw_token:
        return None, None
    settings = get_settings()
    now = datetime.utcnow()
    row = db.scalar(select(SessionRow).where(SessionRow.token_hash == _hash_token(raw_token)))
    if row is None or row.revoked_at is not None or row.expires_at < now:
        return None, None
    if row.last_activity_at + timedelta(days=settings.SESSION_INACTIVITY_DAYS) < now:
        row.revoked_at = now  # expired by inactivity
        db.flush()
        return None, None
    user = db.get(User, row.user_id)
    if user is None or not user.is_active:
        return None, None
    row.last_activity_at = now
    db.flush()
    return user, row


def revoke_session(db: DBSession, row: SessionRow) -> None:
    row.revoked_at = datetime.utcnow()
    db.flush()


def revoke_all_user_sessions(db: DBSession, user_id: int, except_id: int | None = None) -> int:
    rows = db.scalars(select(SessionRow).where(SessionRow.user_id == user_id)).all()
    count = 0
    for row in rows:
        if except_id is not None and row.id == except_id:
            continue
        if row.revoked_at is None:
            row.revoked_at = datetime.utcnow()
            count += 1
    db.flush()
    return count


def cookie_kwargs() -> dict:
    """Secure-by-environment cookie flags.

    Production (cross-origin Netlify→Render) needs SameSite=None + Secure so the
    browser sends the cookie. Localhost dev uses Lax without Secure.
    """
    settings = get_settings()
    production = settings.ENVIRONMENT == "production"
    return {
        "httponly": True,
        "secure": True if production else False,
        "samesite": "none" if production else "lax",
    }
