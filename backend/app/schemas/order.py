from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


ORDER_STATUSES = ("pending", "processing", "on-hold", "completed", "cancelled", "refunded", "failed")


class LineItem(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    quantity: int = Field(ge=1, le=10000)
    price: Decimal = Field(ge=0)


class OrderCreate(BaseModel):
    customer_id: int
    status: str = Field(default="pending", max_length=50)
    total: Optional[Decimal] = Field(default=None, ge=0)
    line_items: Optional[list[LineItem]] = None


class OrderUpdate(BaseModel):
    status: Optional[str] = Field(default=None, max_length=50)
    total: Optional[Decimal] = Field(default=None, ge=0)
    line_items: Optional[list[LineItem]] = None


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    woocommerce_order_id: int
    customer_id: int
    status: str
    payment_status: str = "pending"
    fulfillment_status: str = "unfulfilled"
    order_total: Decimal
    line_items: Optional[Any] = None
    created_at: datetime
    updated_at: datetime


class StatusHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    old_status: Optional[str] = None
    new_status: str
    created_at: datetime


class OrderDetailResponse(OrderResponse):
    status_history: list[StatusHistoryItem] = []


class OrderListResponse(BaseModel):
    items: list[OrderResponse]
    total: int
    page: int
    page_size: int
