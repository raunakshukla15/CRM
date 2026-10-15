from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


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


class OrderListResponse(BaseModel):
    items: list[OrderResponse]
    total: int
    page: int
    page_size: int
