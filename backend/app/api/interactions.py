"""Communications (interactions): per-user records. Manual logging only."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session as DBSession

from app.api.deps import get_client_ip, get_current_user
from app.core.database import get_db
from app.models.customer import Customer
from app.models.interaction import Interaction
from app.models.user import User
from app.schemas.interaction import (
    InteractionCreate,
    InteractionListResponse,
    InteractionResponse,
    InteractionUpdate,
)
from app.services.activity import log_activity

router = APIRouter(prefix="/interactions", tags=["interactions"])


def _serialize(item: Interaction, db: DBSession) -> dict:
    cust = db.get(Customer, item.customer_id)
    return {
        "id": item.id,
        "customer_id": item.customer_id,
        "customer_email": cust.email if cust else None,
        "interaction_type": item.interaction_type,
        "subject": item.subject,
        "description": item.description,
        "outcome": item.outcome,
        "status": item.status,
        "scheduled_at": item.scheduled_at,
        "completed_at": item.completed_at,
        "created_by": item.created_by,
        "created_at": item.created_at,
    }


def _owned_customer_or_404(db: DBSession, customer_id: int, user_id: int) -> Customer:
    customer = db.scalar(
        select(Customer).where(Customer.id == customer_id, Customer.owner_id == user_id)
    )
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.get("", response_model=InteractionListResponse)
def list_interactions(
    user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    customer_id: int | None = Query(default=None),
    interaction_type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    search: str | None = Query(default=None, description="Search subject/description"),
):
    filters = [Interaction.owner_id == user.id]
    if customer_id is not None:
        filters.append(Interaction.customer_id == customer_id)
    if interaction_type is not None:
        filters.append(Interaction.interaction_type == interaction_type)
    if status is not None:
        filters.append(Interaction.status == status)
    if search:
        like = f"%{search}%"
        filters.append((Interaction.subject.like(like)) | (Interaction.description.like(like)))

    query = select(Interaction).where(*filters)
    count_q = select(func.count()).select_from(Interaction).where(*filters)

    total = db.scalar(count_q) or 0
    items = list(
        db.scalars(
            query.order_by(Interaction.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return {
        "items": [_serialize(i, db) for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("", response_model=InteractionResponse, status_code=201)
def create_interaction(
    body: InteractionCreate,
    request: Request,
    user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    if body.interaction_type not in ("call", "email", "meeting", "note"):
        raise HTTPException(status_code=422, detail="Type must be call, email, meeting or note.")
    _owned_customer_or_404(db, body.customer_id, user.id)
    item = Interaction(
        owner_id=user.id,
        customer_id=body.customer_id,
        interaction_type=body.interaction_type,
        subject=body.subject,
        description=body.description,
        outcome=body.outcome,
        status=body.status,
        scheduled_at=body.scheduled_at,
        created_by=body.created_by,
    )
    db.add(item)
    db.flush()
    log_activity(db, "communication.created", f"{body.interaction_type} logged.",
                 user_id=user.id, entity_type="interaction", entity_id=item.id,
                 ip=get_client_ip(request))
    db.commit()
    db.refresh(item)
    return _serialize(item, db)


@router.patch("/{interaction_id}", response_model=InteractionResponse)
def update_interaction(
    interaction_id: int,
    body: InteractionUpdate,
    request: Request,
    user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    item = db.scalar(
        select(Interaction).where(Interaction.id == interaction_id, Interaction.owner_id == user.id)
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Communication not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    log_activity(db, "communication.updated", f"Communication #{item.id} updated.",
                 user_id=user.id, entity_type="interaction", entity_id=item.id,
                 ip=get_client_ip(request))
    db.commit()
    db.refresh(item)
    return _serialize(item, db)


@router.delete("/{interaction_id}")
def delete_interaction(
    interaction_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    item = db.scalar(
        select(Interaction).where(Interaction.id == interaction_id, Interaction.owner_id == user.id)
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Communication not found")
    db.delete(item)
    log_activity(db, "communication.deleted", f"Communication #{interaction_id} deleted.",
                 user_id=user.id, entity_type="interaction", entity_id=interaction_id,
                 ip=get_client_ip(request))
    db.commit()
    return {"ok": True}
