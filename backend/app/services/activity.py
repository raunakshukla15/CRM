"""Append-only activity logging. Backend-only — no API endpoint writes logs."""

from sqlalchemy.orm import Session as DBSession

from app.models.user import ActivityLog


def log_activity(
    db: DBSession,
    action: str,
    description: str = "",
    user_id: int | None = None,
    entity_type: str | None = None,
    entity_id: int | None = None,
    meta: dict | None = None,
    ip: str | None = None,
) -> ActivityLog:
    """Never pass passwords, raw tokens, or secrets in description/meta."""
    row = ActivityLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        meta=meta,
        ip_address=(ip or "")[:64] or None,
    )
    db.add(row)
    db.flush()
    return row
