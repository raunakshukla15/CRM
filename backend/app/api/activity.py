from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session as DBSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import ActivityLog, User
from app.schemas.auth import ActivityListResponse

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("", response_model=ActivityListResponse)
def list_activity(
    user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    action: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
):
    query = select(ActivityLog).where(ActivityLog.user_id == user.id)
    count_q = (
        select(func.count())
        .select_from(ActivityLog)
        .where(ActivityLog.user_id == user.id)
    )
    if action:
        query = query.where(ActivityLog.action == action)
        count_q = count_q.where(ActivityLog.action == action)
    if entity_type:
        query = query.where(ActivityLog.entity_type == entity_type)
        count_q = count_q.where(ActivityLog.entity_type == entity_type)

    total = db.scalar(count_q) or 0
    items = list(
        db.scalars(
            query.order_by(ActivityLog.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}
