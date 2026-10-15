from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.customer import Customer
from app.models.followup import FollowUp, FollowUpStatus
from app.schemas.followup import (
    FollowUpCreate,
    FollowUpListResponse,
    FollowUpResponse,
    FollowUpUpdate,
)

router = APIRouter(prefix="/followups", tags=["followups"])


def _serialize(f: FollowUp, db: Session) -> dict:
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
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(
        default=None, description="pending|completed|cancelled|overdue|upcoming|all"
    ),
    customer_id: int | None = Query(default=None),
):
    now = datetime.utcnow()
    query = select(FollowUp)
    count_q = select(func.count()).select_from(FollowUp)
    filters = []
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
    if filters:
        query = query.where(*filters)
        count_q = count_q.where(*filters)

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
def create_followup(body: FollowUpCreate, db: Session = Depends(get_db)):
    if db.get(Customer, body.customer_id) is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    item = FollowUp(
        customer_id=body.customer_id,
        title=body.title,
        due_date=body.due_date,
        status=FollowUpStatus.PENDING,
        notes=body.notes,
        created_by=body.created_by,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _serialize(item, db)


@router.patch("/{followup_id}", response_model=FollowUpResponse)
def update_followup(followup_id: int, body: FollowUpUpdate, db: Session = Depends(get_db)):
    item = db.get(FollowUp, followup_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    item.status = FollowUpStatus(body.status)
    db.commit()
    db.refresh(item)
    return _serialize(item, db)
