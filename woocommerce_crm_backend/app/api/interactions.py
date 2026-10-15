from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.customer import Customer
from app.models.interaction import Interaction
from app.schemas.interaction import (
    InteractionCreate,
    InteractionListResponse,
    InteractionResponse,
)

router = APIRouter(prefix="/interactions", tags=["interactions"])


@router.get("", response_model=InteractionListResponse)
def list_interactions(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    customer_id: int | None = Query(default=None),
    interaction_type: str | None = Query(default=None),
):
    query = select(Interaction)
    count_q = select(func.count()).select_from(Interaction)
    filters = []
    if customer_id is not None:
        filters.append(Interaction.customer_id == customer_id)
    if interaction_type is not None:
        filters.append(Interaction.interaction_type == interaction_type)
    if filters:
        query = query.where(*filters)
        count_q = count_q.where(*filters)

    total = db.scalar(count_q) or 0
    items = list(
        db.scalars(
            query.order_by(Interaction.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("", response_model=InteractionResponse, status_code=201)
def create_interaction(body: InteractionCreate, db: Session = Depends(get_db)):
    if db.get(Customer, body.customer_id) is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    item = Interaction(
        customer_id=body.customer_id,
        interaction_type=body.interaction_type,
        description=body.description,
        outcome=body.outcome,
        created_by=body.created_by,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
