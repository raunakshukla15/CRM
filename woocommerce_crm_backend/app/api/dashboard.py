from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.customer import Customer, CustomerStatus
from app.models.followup import FollowUp, FollowUpStatus
from app.models.interaction import Interaction
from app.models.order import Order
from app.schemas.dashboard import DashboardResponse

router = APIRouter(tags=["dashboard"])

PENDING_ORDER_STATUSES = ("pending", "on-hold", "processing")


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(db: Session = Depends(get_db)):
    total_customers = db.scalar(select(func.count()).select_from(Customer)) or 0
    total_orders = db.scalar(select(func.count()).select_from(Order)) or 0
    total_revenue = db.scalar(select(func.coalesce(func.sum(Order.order_total), 0))) or 0
    pending_orders = (
        db.scalar(
            select(func.count())
            .select_from(Order)
            .where(Order.status.in_(PENDING_ORDER_STATUSES))
        )
        or 0
    )
    vip_customers = (
        db.scalar(
            select(func.count())
            .select_from(Customer)
            .where(Customer.customer_status == CustomerStatus.VIP)
        )
        or 0
    )

    now = datetime.utcnow()
    overdue_followups = (
        db.scalar(
            select(func.count())
            .select_from(FollowUp)
            .where(FollowUp.status == FollowUpStatus.PENDING, FollowUp.due_date < now)
        )
        or 0
    )
    upcoming_followups = (
        db.scalar(
            select(func.count())
            .select_from(FollowUp)
            .where(FollowUp.status == FollowUpStatus.PENDING, FollowUp.due_date >= now)
        )
        or 0
    )

    recent_orders_rows = db.execute(
        select(Order, Customer.email)
        .outerjoin(Customer, Customer.id == Order.customer_id)
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
            .where(FollowUp.status == FollowUpStatus.PENDING, FollowUp.due_date < now)
            .order_by(FollowUp.due_date.asc())
            .limit(5)
        ).all()
    )
    upcoming = list(
        db.scalars(
            select(FollowUp)
            .where(FollowUp.status == FollowUpStatus.PENDING, FollowUp.due_date >= now)
            .order_by(FollowUp.due_date.asc())
            .limit(5)
        ).all()
    )

    recent_interactions = list(
        db.scalars(select(Interaction).order_by(Interaction.id.desc()).limit(8)).all()
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
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "pending_orders": pending_orders,
            "vip_customers": vip_customers,
            "overdue_followups": overdue_followups,
            "upcoming_followups": upcoming_followups,
        },
        "recent_orders": recent_orders,
        "overdue_followups": [followup_dict(f) for f in overdue],
        "upcoming_followups": [followup_dict(f) for f in upcoming],
        "recent_activity": recent_activity,
    }
