from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session as DBSession

from app.api.deps import get_client_ip, get_current_user
from app.core.database import get_db
from app.models.customer import Customer
from app.models.followup import FollowUp, FollowUpStatus
from app.models.user import User
from app.schemas.followup import (
    FollowUpCreate,
    FollowUpListResponse,
    FollowUpResponse,
    FollowUpUpdate,
)
from app.services.activity import log_activity

router = APIRouter(prefix="/followups", tags=["followups"])


def _serialize(f: FollowUp, db: DBSession) -> dict:
    now = datetime.utcnow()
    cust = db.get(Customer, f.customer_id)
    return {
        "id": f.id,
        "customer_id": f.customer_id,
        "title": f.title,
        "due_date": f.due_date,
        "status": f.status.value if isinstance(f.status, FollowUpStatus) else f.status,
        "is_overdue": f.status == FollowUpStatus.PENDING and f.due_date < now,
        "notes": f.notes,
        "created_by": f.created_by,
        "created_at": f.created_at,
        "updated_at": f.updated_at,
        "customer_email": cust.email if cust else None,
    }


@router.get("", response_model=FollowUpListResponse)
def list_followups(
    user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(
        default=None, description="pending|completed|cancelled|overdue|upcoming|all"
    ),
    customer_id: int | None = Query(default=None),
):
    now = datetime.utcnow()
    filters = [FollowUp.owner_id == user.id]
    if customer_id is not None:
        filters.append(FollowUp.customer_id == customer_id)
    if status and status != "all":
        if status == "overdue":
            filters.append(FollowUp.status == FollowUpStatus.PENDING)
            filters.append(FollowUp.due_date < now)
        elif status == "upcoming":
            filters.append(FollowUp.status == FollowUpStatus.PENDING)
            filters.append(FollowUp.due_date >= now)
        elif status in ("pending", "completed", "cancelled"):
            filters.append(FollowUp.status == FollowUpStatus(status))
        else:
            raise HTTPException(status_code=400, detail=f"Unknown status filter: {status}")

    query = select(FollowUp).where(*filters)
    count_q = select(func.count()).select_from(FollowUp).where(*filters)

    total = db.scalar(count_q) or 0
    items = list(
        db.scalars(
            query.order_by(FollowUp.due_date.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return {
        "items": [_serialize(f, db) for f in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("", response_model=FollowUpResponse, status_code=201)
def create_followup(
    body: FollowUpCreate,
    request: Request,
    user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    customer = db.scalar(
        select(Customer).where(Customer.id == body.customer_id, Customer.owner_id == user.id)
    )
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    item = FollowUp(
        owner_id=user.id,
        customer_id=body.customer_id,
        title=body.title,
        due_date=body.due_date,
        status=FollowUpStatus.PENDING,
        notes=body.notes,
        created_by=body.created_by,
    )
    db.add(item)
    db.flush()
    log_activity(db, "followup.created", f"Follow-up '{body.title}' created.",
                 user_id=user.id, entity_type="followup", entity_id=item.id,
                 ip=get_client_ip(request))
    db.commit()
    db.refresh(item)
    return _serialize(item, db)


@router.patch("/{followup_id}", response_model=FollowUpResponse)
def update_followup(
    followup_id: int,
    body: FollowUpUpdate,
    request: Request,
    user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    item = db.scalar(
        select(FollowUp).where(FollowUp.id == followup_id, FollowUp.owner_id == user.id)
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    item.status = FollowUpStatus(body.status)
    log_activity(db, "followup.updated", f"Follow-up '{item.title}' → {body.status}.",
                 user_id=user.id, entity_type="followup", entity_id=item.id,
                 ip=get_client_ip(request))
    db.commit()
    db.refresh(item)
    return _serialize(item, db)


@router.delete("/{followup_id}")
def delete_followup(
    followup_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    item = db.scalar(
        select(FollowUp).where(FollowUp.id == followup_id, FollowUp.owner_id == user.id)
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    db.delete(item)
    log_activity(db, "followup.deleted", f"Follow-up #{followup_id} deleted.",
                 user_id=user.id, entity_type="followup", entity_id=followup_id,
                 ip=get_client_ip(request))
    db.commit()
    return {"ok": True}
