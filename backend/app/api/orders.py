"""Orders: per-user CRUD with backend-computed totals and status history."""

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session as DBSession

from app.api.deps import get_client_ip, get_current_user
from app.core.database import get_db
from app.models.customer import Customer
from app.models.order import Order
from app.models.order_status_history import OrderStatusHistory
from app.models.user import User
from app.schemas.order import (
    ORDER_STATUSES,
    OrderCreate,
    OrderDetailResponse,
    OrderListResponse,
    OrderResponse,
    OrderUpdate,
)
from app.services.activity import log_activity
from app.services.crm_service import recalc_customer_aggregates

router = APIRouter(prefix="/orders", tags=["orders"])


def _owned_order_or_404(db: DBSession, order_id: int, user_id: int) -> Order:
    order = db.scalar(
        select(Order).where(Order.id == order_id, Order.owner_id == user_id)
    )
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


def _owned_customer_or_404(db: DBSession, customer_id: int, user_id: int) -> Customer:
    customer = db.scalar(
        select(Customer).where(Customer.id == customer_id, Customer.owner_id == user_id)
    )
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


def _compute_total(body_total, line_items) -> Decimal:
    if line_items:
        return sum((li.price * li.quantity for li in line_items), Decimal("0"))
    if body_total is None:
        raise HTTPException(status_code=422, detail="Provide either total or line_items.")
    return body_total


@router.get("", response_model=OrderListResponse)
def list_orders(
    user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    customer_id: int | None = Query(default=None),
    status: str | None = Query(default=None),
    search: str | None = Query(default=None, description="Search by WooCommerce order ID"),
    sort: str = Query(default="newest", description="newest|total"),
):
    filters = [Order.owner_id == user.id]
    if customer_id is not None:
        filters.append(Order.customer_id == customer_id)
    if status is not None:
        filters.append(Order.status == status)
    if search:
        filters.append(Order.woocommerce_order_id.like(f"%{search}%"))

    query = select(Order).where(*filters)
    count_q = select(func.count()).select_from(Order).where(*filters)
    query = query.order_by(Order.order_total.desc()) if sort == "total" else query.order_by(Order.id.desc())

    total = db.scalar(count_q) or 0
    items = list(db.scalars(query.offset((page - 1) * page_size).limit(page_size)).all())
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("", response_model=OrderResponse, status_code=201)
def create_order(
    body: OrderCreate,
    request: Request,
    user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    if body.status not in ORDER_STATUSES:
        raise HTTPException(status_code=422, detail=f"Invalid status. Use one of: {ORDER_STATUSES}")
    customer = _owned_customer_or_404(db, body.customer_id, user.id)
    total = _compute_total(body.total, body.line_items)

    # Allocate a store-facing order number from a per-table sequence position.
    max_wc = db.scalar(select(func.max(Order.woocommerce_order_id))) or 0
    order = Order(
        owner_id=user.id,
        woocommerce_order_id=int(max_wc) + 1,
        customer_id=customer.id,
        status=body.status,
        payment_status="paid" if body.status in ("completed", "processing") else "pending",
        fulfillment_status="fulfilled" if body.status == "completed" else "unfulfilled",
        order_total=total,
        line_items=[li.model_dump(mode="json") for li in body.line_items] if body.line_items else None,
    )
    db.add(order)
    db.flush()
    db.add(OrderStatusHistory(order_id=order.id, old_status=None, new_status=order.status,
                              changed_by_user_id=user.id))
    recalc_customer_aggregates(db, customer)
    log_activity(db, "order.created", f"Order #{order.woocommerce_order_id} ({total}) created.",
                 user_id=user.id, entity_type="order", entity_id=order.id,
                 ip=get_client_ip(request))
    db.commit()
    db.refresh(order)
    return order


@router.get("/{order_id}", response_model=OrderDetailResponse)
def get_order(
    order_id: int,
    user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    order = _owned_order_or_404(db, order_id, user.id)
    history = list(
        db.scalars(
            select(OrderStatusHistory)
            .where(OrderStatusHistory.order_id == order.id)
            .order_by(OrderStatusHistory.id.asc())
        ).all()
    )
    payload = OrderResponse.model_validate(order).model_dump()
    payload["status_history"] = [
        {"id": h.id, "old_status": h.old_status, "new_status": h.new_status, "created_at": h.created_at}
        for h in history
    ]
    return payload


@router.patch("/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: int,
    body: OrderUpdate,
    request: Request,
    user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    order = _owned_order_or_404(db, order_id, user.id)
    if body.status is not None:
        if body.status not in ORDER_STATUSES:
            raise HTTPException(status_code=422, detail=f"Invalid status. Use one of: {ORDER_STATUSES}")
        if body.status != order.status:
            db.add(OrderStatusHistory(order_id=order.id, old_status=order.status,
                                      new_status=body.status, changed_by_user_id=user.id))
            order.status = body.status
            log_activity(db, "order.status_changed",
                         f"Order #{order.woocommerce_order_id} → {body.status}.",
                         user_id=user.id, entity_type="order", entity_id=order.id,
                         ip=get_client_ip(request))
    if body.line_items is not None:
        order.order_total = _compute_total(None, body.line_items)
        order.line_items = [li.model_dump(mode="json") for li in body.line_items]
    elif body.total is not None:
        order.order_total = body.total
    recalc_customer_aggregates(db, order.customer)
    db.commit()
    db.refresh(order)
    return order


@router.delete("/{order_id}")
def delete_order(
    order_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    order = _owned_order_or_404(db, order_id, user.id)
    customer = order.customer
    wc_id = order.woocommerce_order_id
    db.delete(order)
    db.flush()
    if customer is not None:
        recalc_customer_aggregates(db, customer)
    log_activity(db, "order.deleted", f"Order #{wc_id} deleted.",
                 user_id=user.id, entity_type="order", entity_id=order_id,
                 ip=get_client_ip(request))
    db.commit()
    return {"ok": True}
