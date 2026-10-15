from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class FollowUpCreate(BaseModel):
    customer_id: int
    title: str = Field(min_length=1, max_length=255)
    due_date: datetime
    notes: Optional[str] = Field(default=None, max_length=5000)
    created_by: str = Field(default="admin", max_length=100)


class FollowUpUpdate(BaseModel):
    status: str = Field(pattern="^(pending|completed|cancelled)$")


class FollowUpResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    title: str
    due_date: datetime
    status: str
    is_overdue: bool = False
    notes: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: datetime
    customer_email: Optional[str] = None


class FollowUpListResponse(BaseModel):
    items: list[FollowUpResponse]
    total: int
    page: int
    page_size: int
