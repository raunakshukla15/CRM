from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class InteractionCreate(BaseModel):
    customer_id: int
    interaction_type: str = Field(default="note", max_length=50)
    description: str = Field(min_length=1, max_length=5000)
    outcome: Optional[str] = Field(default=None, max_length=100)
    created_by: str = Field(default="admin", max_length=100)


class InteractionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    interaction_type: str
    description: str
    outcome: Optional[str] = None
    created_by: str
    created_at: datetime


class InteractionListResponse(BaseModel):
    items: list[InteractionResponse]
    total: int
    page: int
    page_size: int
