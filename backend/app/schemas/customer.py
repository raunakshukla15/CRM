from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.customer import CustomerStatus


class CustomerBase(BaseModel):
    email: EmailStr
    first_name: str = Field(default="", max_length=100)
    last_name: str = Field(default="", max_length=100)
    phone: Optional[str] = Field(default=None, max_length=50)
    company: Optional[str] = Field(default=None, max_length=255)
    billing_address: Optional[dict[str, Any]] = None
    shipping_address: Optional[dict[str, Any]] = None
    profile_notes: Optional[str] = Field(default=None, max_length=5000)


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=50)
    company: Optional[str] = Field(default=None, max_length=255)
    billing_address: Optional[dict[str, Any]] = None
    shipping_address: Optional[dict[str, Any]] = None
    profile_profile_notes: Optional[str] = Field(default=None, max_length=5000)
    customer_status: Optional[CustomerStatus] = None


class CustomerResponse(CustomerBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    woocommerce_customer_id: Optional[int] = None
    total_spend: Decimal
    lifetime_orders: int
    customer_status: CustomerStatus
    created_at: datetime
    updated_at: datetime


class CustomerListResponse(BaseModel):
    items: list[CustomerResponse]
    total: int
    page: int
    page_size: int


class CommunicationLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    message_type: str
    recipient_email: str
    status: str
    payload: Optional[dict[str, Any]] = None
    sent_at: datetime


class OrderBriefResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    woocommerce_order_id: int
    status: str
    payment_status: str = "pending"
    fulfillment_status: str = "unfulfilled"
    order_total: Decimal
    line_items: Optional[Any] = None
    created_at: datetime
    updated_at: datetime


class InteractionBriefResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    interaction_type: str
    description: str
    outcome: Optional[str] = None
    created_by: str
    created_at: datetime


class FollowUpBriefResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    due_date: datetime
    status: str
    notes: Optional[str] = None
    created_at: datetime


class NoteCreate(BaseModel):
    note: str = Field(min_length=1, max_length=5000)
    created_by: str = Field(default="admin", max_length=100)


class NoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    note: str
    created_by: str
    created_at: datetime


class CustomerDetailResponse(CustomerResponse):
    orders: list[OrderBriefResponse] = []
    communication_logs: list[CommunicationLogResponse] = []
    notes: list[NoteResponse] = []
    interactions: list[InteractionBriefResponse] = []
    followups: list[FollowUpBriefResponse] = []
