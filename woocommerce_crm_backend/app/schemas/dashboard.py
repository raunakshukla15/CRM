from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_customers: int
    total_orders: int
    total_revenue: Decimal
    pending_orders: int
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


class DashboardResponse(BaseModel):
    stats: DashboardStats
    recent_orders: list[RecentOrderItem]
    overdue_followups: list[dict[str, Any]]
    upcoming_followups: list[dict[str, Any]]
    recent_activity: list[dict[str, Any]]


class WooStatusResponse(BaseModel):
    configured: bool
    mode: str  # "live" | "demo"
    store_url: Optional[str] = None
    key_hint: Optional[str] = None
    last_sync_at: Optional[datetime] = None
    customers_synced: int = 0
    orders_synced: int = 0
    message: Optional[str] = None


class WooSyncResponse(BaseModel):
    ok: bool
    mode: str
    customers_synced: int
    orders_synced: int
    message: str
    last_sync_at: Optional[datetime] = None
