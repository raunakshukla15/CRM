from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class InteractionCreate(BaseModel):
    customer_id: int
    interaction_type: str = Field(default="note", max_length=50)
    subject: Optional[str] = Field(default=None, max_length=255)
    description: str = Field(min_length=1, max_length=5000)
    outcome: Optional[str] = Field(default=None, max_length=100)
    status: str = Field(default="logged", max_length=50)
    scheduled_at: Optional[datetime] = None
    created_by: str = Field(default="admin", max_length=100)


class InteractionUpdate(BaseModel):
    interaction_type: Optional[str] = Field(default=None, max_length=50)
    subject: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None, min_length=1, max_length=5000)
    outcome: Optional[str] = Field(default=None, max_length=100)
    status: Optional[str] = Field(default=None, max_length=50)
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class InteractionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    customer_email: Optional[str] = None
    interaction_type: str
    subject: Optional[str] = None
    description: str
    outcome: Optional[str] = None
    status: str
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: str
    created_at: datetime


class InteractionListResponse(BaseModel):
    items: list[InteractionResponse]
    total: int
    page: int
    page_size: int
