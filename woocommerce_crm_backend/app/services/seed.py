"""Demo seed data — realistic CRM records used when no WooCommerce store is connected.

Idempotent: does nothing if customers already exist (unless force=True).
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.customer import Customer, CustomerStatus
from app.models.followup import FollowUp, FollowUpStatus
from app.models.interaction import Interaction
from app.models.order import Order
from app.services.woocommerce import _record_sync, derive_fulfillment_status, derive_payment_status

logger = logging.getLogger(__name__)

DEMO_CUSTOMERS = [
    {"wc": 101, "email": "jane.doe@example.com", "first": "Jane", "last": "Doe", "phone": "+1-555-0100", "city": "San Francisco"},
    {"wc": 102, "email": "marcus.chen@example.com", "first": "Marcus", "last": "Chen", "phone": "+1-555-0101", "city": "Austin"},
    {"wc": 103, "email": "priya.nair@example.com", "first": "Priya", "last": "Nair", "phone": "+1-555-0102", "city": "Seattle"},
    {"wc": 104, "email": "tomi.ade@example.com", "first": "Tomi", "last": "Ade", "phone": "+1-555-0103", "city": "Chicago"},
    {"wc": 105, "email": "lucia.rossi@example.com", "first": "Lucia", "last": "Rossi", "phone": "+1-555-0104", "city": "Boston"},
    {"wc": 106, "email": "omar.haddad@example.com", "first": "Omar", "last": "Haddad", "phone": "+1-555-0105", "city": "Denver"},
    {"wc": 107, "email": "sofia.meyer@example.com", "first": "Sofia", "last": "Meyer", "phone": "+1-555-0106", "city": "Portland"},
    {"wc": 108, "email": "liam.wong@example.com", "first": "Liam", "last": "Wong", "phone": "+1-555-0107", "city": "New York"},
]

DEMO_ORDERS = [
    # (wc_order_id, customer_wc_id, status, total, days_ago)
    (5001, 101, "completed", "320.00", 21),
    (5002, 101, "completed", "250.00", 6),
    (5003, 102, "processing", "149.99", 2),
    (5004, 103, "completed", "89.50", 14),
    (5005, 103, "completed", "210.00", 3),
    (5006, 104, "pending", "59.00", 1),
    (5007, 105, "completed", "640.00", 30),
    (5008, 105, "completed", "120.00", 9),
    (5009, 106, "on-hold", "75.25", 4),
    (5010, 107, "completed", "199.00", 12),
    (5011, 108, "processing", "310.00", 1),
    (5012, 102, "completed", "45.00", 40),
]


def seed_demo_data(db: Session, force: bool = False) -> dict:
    existing = db.scalar(select(func.count()).select_from(Customer)) or 0
    if existing and not force:
        return {"mode": "demo", "seeded": False, "message": f"Database already has {existing} customers — skipping seed."}

    now = datetime.utcnow()
    by_wc: dict[int, Customer] = {}
    for c in DEMO_CUSTOMERS:
        customer = Customer(
            woocommerce_customer_id=c["wc"],
            email=c["email"],
            first_name=c["first"],
            last_name=c["last"],
            phone=c["phone"],
            billing_address={"city": c["city"], "country": "US"},
            shipping_address={"city": c["city"], "country": "US"},
            customer_status=CustomerStatus.LEAD,
        )
        db.add(customer)
        by_wc[c["wc"]] = customer
    db.flush()

    for wc_id, cust_wc, status, total, days_ago in DEMO_ORDERS:
        customer = by_wc[cust_wc]
        created = now - timedelta(days=days_ago)
        order = Order(
            woocommerce_order_id=wc_id,
            customer_id=customer.id,
            status=status,
            payment_status=derive_payment_status(status),
            fulfillment_status=derive_fulfillment_status(status),
            order_total=Decimal(total),
            line_items=[{"name": "Demo product", "quantity": 1, "total": total}],
            created_at=created,
        )
        db.add(order)
    db.flush()

    # Recompute aggregates + VIP promotion
    from app.services.crm_service import recalc_customer_aggregates

    for customer in by_wc.values():
        recalc_customer_aggregates(db, customer)
    db.flush()

    # Interactions (communication timeline)
    jane = by_wc[101]
    db.add_all(
        [
            Interaction(customer_id=jane.id, interaction_type="call", description="Called about delayed shipment; customer satisfied with resolution.", outcome="positive", created_by="admin"),
            Interaction(customer_id=jane.id, interaction_type="email", description="Sent VIP discount code after crossing $500 spend.", outcome="sent", created_by="admin"),
            Interaction(customer_id=by_wc[103].id, interaction_type="meeting", description="Demo call for bulk order pricing.", outcome="follow-up needed", created_by="admin"),
        ]
    )

    # Follow-ups: one overdue, two upcoming, one completed
    db.add_all(
        [
            FollowUp(customer_id=jane.id, title="Send loyalty discount code", due_date=now - timedelta(days=2), status=FollowUpStatus.PENDING, notes="Jane crossed VIP threshold."),
            FollowUp(customer_id=by_wc[102].id, title="Confirm payment for order #5003", due_date=now + timedelta(days=1), status=FollowUpStatus.PENDING, notes="Processing order awaiting payment."),
            FollowUp(customer_id=by_wc[106].id, title="Follow up on on-hold order #5009", due_date=now + timedelta(days=3), status=FollowUpStatus.PENDING),
            FollowUp(customer_id=by_wc[105].id, title="Thank-you call for $640 order", due_date=now - timedelta(days=5), status=FollowUpStatus.COMPLETED, notes="Done — customer happy."),
        ]
    )
    db.flush()

    customers = len(DEMO_CUSTOMERS)
    orders = len(DEMO_ORDERS)
    _record_sync(db, mode="demo", customers=customers, orders=orders,
                 message=f"Demo data loaded: {customers} customers, {orders} orders")
    db.commit()
    logger.info("Seeded demo data: %s customers, %s orders", customers, orders)
    return {"mode": "demo", "seeded": True, "customers_synced": customers, "orders_synced": orders,
            "message": f"Demo data loaded: {customers} customers, {orders} orders"}
