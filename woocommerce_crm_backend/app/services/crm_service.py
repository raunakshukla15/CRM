"""Core CRM upsert logic — idempotent ingestion of WooCommerce events."""

import logging
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.communication_log import CommunicationLog, CommunicationStatus
from app.models.customer import Customer, CustomerStatus
from app.models.order import Order
from app.services.email_sender import send_email

logger = logging.getLogger(__name__)


def _as_decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0"))
    except Exception:
        return Decimal("0")


def log_communication(
    db: Session,
    customer_id: int,
    message_type: str,
    recipient_email: str,
    ok: bool,
    payload: dict | None = None,
) -> CommunicationLog:
    entry = CommunicationLog(
        customer_id=customer_id,
        message_type=message_type,
        recipient_email=recipient_email,
        status=CommunicationStatus.SENT if ok else CommunicationStatus.FAILED,
        payload=payload or {},
    )
    db.add(entry)
    db.flush()
    return entry


def send_and_log(
    db: Session,
    customer: Customer,
    message_type: str,
    subject: str,
    body: str,
) -> bool:
    ok = send_email(customer.email, subject, body)
    log_communication(
        db,
        customer_id=customer.id,
        message_type=message_type,
        recipient_email=customer.email,
        ok=ok,
        payload={"subject": subject, "body": body},
    )
    return ok


def recalc_customer_aggregates(db: Session, customer: Customer) -> None:
    """Recompute total_spend + lifetime_orders and apply VIP promotion."""
    settings = get_settings()
    total, count = db.execute(
        select(
            func.coalesce(func.sum(Order.order_total), 0),
            func.count(Order.id),
        ).where(Order.customer_id == customer.id)
    ).one()

    customer.total_spend = Decimal(total or 0)
    customer.lifetime_orders = int(count or 0)

    # Auto-promote to VIP at threshold; demote only if explicitly churned? No —
    # keep it monotonic except churned handling stays manual.
    if customer.total_spend >= Decimal(str(settings.VIP_SPEND_THRESHOLD)):
        if customer.customer_status != CustomerStatus.VIP:
            logger.info(
                "Promoting customer %s to VIP (spend=%s)", customer.id, customer.total_spend
            )
        customer.customer_status = CustomerStatus.VIP
    elif customer.customer_status == CustomerStatus.LEAD and customer.lifetime_orders > 0:
        customer.customer_status = CustomerStatus.ACTIVE


def upsert_customer_from_webhook(db: Session, payload: dict) -> tuple[Customer, bool]:
    """Handle customer.created / customer.updated. Returns (customer, created)."""
    wc_id = payload.get("id")
    email = (payload.get("email") or "").strip().lower()

    if not email and wc_id is None:
        raise ValueError("Customer payload requires at least an email or id")

    customer: Customer | None = None
    if wc_id is not None:
        customer = db.scalar(select(Customer).where(Customer.woocommerce_customer_id == wc_id))
    if customer is None and email:
        customer = db.scalar(select(Customer).where(Customer.email == email))

    created = customer is None
    if created:
        customer = Customer(
            woocommerce_customer_id=wc_id,
            email=email,
            customer_status=CustomerStatus.LEAD,
        )
        db.add(customer)

    # Update mutable fields (don't overwrite with blanks on partial updates)
    if wc_id is not None:
        customer.woocommerce_customer_id = wc_id
    if email:
        customer.email = email
    if payload.get("first_name") is not None:
        customer.first_name = payload.get("first_name") or ""
    if payload.get("last_name") is not None:
        customer.last_name = payload.get("last_name") or ""
    if payload.get("phone") is not None:
        customer.phone = payload.get("phone") or None
    if payload.get("billing") is not None:
        customer.billing_address = payload.get("billing")
    if payload.get("shipping") is not None:
        customer.shipping_address = payload.get("shipping")

    db.flush()

    if created and customer.email:
        first = customer.first_name or "there"
        send_and_log(
            db,
            customer,
            message_type="WELCOME_EMAIL",
            subject="Welcome to our store!",
            body=(
                f"Hi {first},\n\nThanks for creating an account with us. "
                "We're glad to have you!\n\n— The Store Team"
            ),
        )

    return customer, created


def _resolve_order_customer(db: Session, payload: dict) -> Customer:
    """Find or create the Customer for an order payload."""
    billing = payload.get("billing") or {}
    email = ((payload.get("billing") or {}).get("email") or "").strip().lower()
    wc_customer_id = payload.get("customer_id") or None  # 0 => guest in WooCommerce

    customer: Customer | None = None
    if wc_customer_id:
        customer = db.scalar(
            select(Customer).where(Customer.woocommerce_customer_id == wc_customer_id)
        )
    if customer is None and email:
        customer = db.scalar(select(Customer).where(Customer.email == email))

    if customer is None:
        if not email:
            raise ValueError("Order payload has no customer email and no known customer_id")
        customer = Customer(
            woocommerce_customer_id=wc_customer_id or None,
            email=email,
            first_name=billing.get("first_name") or "",
            last_name=billing.get("last_name") or "",
            phone=billing.get("phone"),
            billing_address=billing or None,
            shipping_address=payload.get("shipping") or None,
            customer_status=CustomerStatus.LEAD,
        )
        db.add(customer)
        db.flush()
        # Guest-turned-customer also gets a welcome email
        send_and_log(
            db,
            customer,
            message_type="WELCOME_EMAIL",
            subject="Welcome to our store!",
            body=(
                f"Hi {customer.first_name or 'there'},\n\n"
                "Thanks for your first order! An account profile was created for you.\n\n"
                "— The Store Team"
            ),
        )
    return customer


def upsert_order_from_webhook(
    db: Session, payload: dict
) -> tuple[Order, Customer, bool, bool]:
    """Handle order.created / order.updated.

    Returns (order, customer, order_created, became_completed).
    Idempotent on woocommerce_order_id.
    """
    wc_order_id = payload.get("id")
    if wc_order_id is None:
        raise ValueError("Order payload requires an id")

    new_status = str(payload.get("status") or "pending")
    order_total = _as_decimal(payload.get("total"))
    line_items = payload.get("line_items")

    order = db.scalar(select(Order).where(Order.woocommerce_order_id == wc_order_id))
    order_created = order is None
    previous_status = order.status if order else None

    if order_created:
        customer = _resolve_order_customer(db, payload)
        order = Order(
            woocommerce_order_id=wc_order_id,
            customer_id=customer.id,
            status=new_status,
            order_total=order_total,
            line_items=line_items,
        )
        db.add(order)
    else:
        order.status = new_status
        order.order_total = order_total
        order.line_items = line_items
        customer = order.customer

    db.flush()
    recalc_customer_aggregates(db, customer)
    db.flush()

    became_completed = previous_status != "completed" and new_status == "completed"
    if became_completed:
        send_and_log(
            db,
            customer,
            message_type="ORDER_COMPLETED_EMAIL",
            subject=f"Thank you for order #{wc_order_id}!",
            body=(
                f"Hi {customer.first_name or 'there'},\n\n"
                f"Your order #{wc_order_id} (total {order_total}) is now completed. "
                "Thanks for shopping with us!\n\n— The Store Team"
            ),
        )

    return order, customer, order_created, became_completed
