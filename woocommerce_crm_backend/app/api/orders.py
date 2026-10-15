from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.order import Order
from app.schemas.order import OrderListResponse

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=OrderListResponse)
def list_orders(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    customer_id: int | None = Query(default=None),
    status: str | None = Query(default=None),
    search: str | None = Query(default=None, description="Search by WooCommerce order ID"),
):
    query = select(Order)
    count_q = select(func.count()).select_from(Order)
    filters = []
    if customer_id is not None:
        filters.append(Order.customer_id == customer_id)
    if status is not None:
        filters.append(Order.status == status)
    if search:
        like = f"%{search}%"
        filters.append(Order.woocommerce_order_id.like(like))
    if filters:
        query = query.where(*filters)
        count_q = count_q.where(*filters)

    total = db.scalar(count_q) or 0
    items = list(
        db.scalars(
            query.order_by(Order.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}
