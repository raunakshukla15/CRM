from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_customers: int
    new_customers: int = 0
    total_orders: int
    total_revenue: Decimal
    pending_orders: int
    completed_orders: int = 0
    vip_customers: int
    overdue_followups: int
    upcoming_followups: int


class RecentOrderItem(BaseModel):
    id: int
    woocommerce_order_id: int
    customer_id: int
    customer_email: Optional[str] = None
    status: str
    order_total: Decimal
    created_at: datetime


class RecentCustomerItem(BaseModel):
    id: int
    email: str
    first_name: str = ""
    last_name: str = ""
    created_at: datetime


class DashboardResponse(BaseModel):
    stats: DashboardStats
    recent_orders: list[RecentOrderItem]
    recent_customers: list[RecentCustomerItem] = []
    overdue_followups: list[dict[str, Any]]
    upcoming_followups: list[dict[str, Any]]
    recent_activity: list[dict[str, Any]]
    orders_by_day: list[dict[str, Any]] = []
