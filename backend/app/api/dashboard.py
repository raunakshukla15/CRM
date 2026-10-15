from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session as DBSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.customer import Customer, CustomerStatus
from app.models.followup import FollowUp, FollowUpStatus
from app.models.interaction import Interaction
from app.models.order import Order
from app.models.user import User
from app.schemas.dashboard import DashboardResponse

router = APIRouter(tags=["dashboard"])

PENDING_ORDER_STATUSES = ("pending", "on-hold", "processing")


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
    date_from: datetime | None = Query(default=None, description="Filter orders/customers from"),
    date_to: datetime | None = Query(default=None, description="Filter orders/customers to"),
):
    uid = user.id
    now = datetime.utcnow()

    order_time_filters = [Order.owner_id == uid]
    customer_time_filters = [Customer.owner_id == uid]
    if date_from:
        order_time_filters.append(Order.created_at >= date_from)
        customer_time_filters.append(Customer.created_at >= date_from)
    if date_to:
        order_time_filters.append(Order.created_at <= date_to)
        customer_time_filters.append(Customer.created_at <= date_to)

    def count_orders(*extra):
        return db.scalar(select(func.count()).select_from(Order).where(*order_time_filters, *extra)) or 0

    def count_customers(*extra):
        return db.scalar(select(func.count()).select_from(Customer).where(*customer_time_filters, *extra)) or 0

    total_customers = count_customers()
    total_orders = count_orders()
    total_revenue = db.scalar(select(func.coalesce(func.sum(Order.order_total), 0)).where(*order_time_filters)) or 0
    pending_orders = count_orders(Order.status.in_(PENDING_ORDER_STATUSES))
    completed_orders = count_orders(Order.status == "completed")
    vip_customers = count_customers(Customer.customer_status == CustomerStatus.VIP)
    new_customers = count_customers(Customer.created_at >= now - timedelta(days=30))

    overdue_followups = (
        db.scalar(
            select(func.count()).select_from(FollowUp).where(
                FollowUp.owner_id == uid, FollowUp.status == FollowUpStatus.PENDING,
                FollowUp.due_date < now)
        ) or 0
    )
    upcoming_followups = (
        db.scalar(
            select(func.count()).select_from(FollowUp).where(
                FollowUp.owner_id == uid, FollowUp.status == FollowUpStatus.PENDING,
                FollowUp.due_date >= now)
        ) or 0
    )

    # Orders per day (last 14 days, owned) for the chart.
    since = now - timedelta(days=13)
    per_day = db.execute(
        select(func.date(Order.created_at), func.count(), func.coalesce(func.sum(Order.order_total), 0))
        .where(Order.owner_id == uid, Order.created_at >= since)
        .group_by(func.date(Order.created_at))
        .order_by(func.date(Order.created_at).asc())
    ).all()
    orders_by_day = [
        {"date": str(day), "orders": int(n), "revenue": float(rev or 0)} for day, n, rev in per_day
    ]

    recent_orders_rows = db.execute(
        select(Order, Customer.email)
        .outerjoin(Customer, Customer.id == Order.customer_id)
        .where(Order.owner_id == uid)
        .order_by(Order.id.desc())
        .limit(5)
    ).all()
    recent_orders = [
        {
            "id": o.id,
            "woocommerce_order_id": o.woocommerce_order_id,
            "customer_id": o.customer_id,
            "customer_email": email,
            "status": o.status,
            "order_total": o.order_total,
            "created_at": o.created_at,
        }
        for o, email in recent_orders_rows
    ]

    recent_customers_rows = list(
        db.scalars(
            select(Customer).where(Customer.owner_id == uid).order_by(Customer.id.desc()).limit(5)
        ).all()
    )
    recent_customers = [
        {"id": c.id, "email": c.email, "first_name": c.first_name, "last_name": c.last_name,
         "created_at": c.created_at}
        for c in recent_customers_rows
    ]

    def followup_dict(f: FollowUp) -> dict:
        cust = db.get(Customer, f.customer_id)
        return {
            "id": f.id,
            "title": f.title,
            "due_date": f.due_date.isoformat() if f.due_date else None,
            "status": f.status.value,
            "customer_id": f.customer_id,
            "customer_email": cust.email if cust else None,
        }

    overdue = list(
        db.scalars(
            select(FollowUp)
            .where(FollowUp.owner_id == uid, FollowUp.status == FollowUpStatus.PENDING,
                   FollowUp.due_date < now)
            .order_by(FollowUp.due_date.asc())
            .limit(5)
        ).all()
    )
    upcoming = list(
        db.scalars(
            select(FollowUp)
            .where(FollowUp.owner_id == uid, FollowUp.status == FollowUpStatus.PENDING,
                   FollowUp.due_date >= now)
            .order_by(FollowUp.due_date.asc())
            .limit(5)
        ).all()
    )

    recent_interactions = list(
        db.scalars(
            select(Interaction).where(Interaction.owner_id == uid)
            .order_by(Interaction.id.desc()).limit(8)
        ).all()
    )
    recent_activity = [
        {
            "kind": "interaction",
            "id": i.id,
            "text": f"{i.interaction_type}: {i.description[:80]}",
            "customer_id": i.customer_id,
            "at": i.created_at.isoformat() if i.created_at else None,
        }
        for i in recent_interactions
    ]

    return {
        "stats": {
            "total_customers": total_customers,
            "new_customers": new_customers,
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "pending_orders": pending_orders,
            "completed_orders": completed_orders,
            "vip_customers": vip_customers,
            "overdue_followups": overdue_followups,
            "upcoming_followups": upcoming_followups,
        },
        "recent_orders": recent_orders,
        "recent_customers": recent_customers,
        "overdue_followups": [followup_dict(f) for f in overdue],
        "upcoming_followups": [followup_dict(f) for f in upcoming],
        "recent_activity": recent_activity,
        "orders_by_day": orders_by_day,
    }
