"""Notification schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: int
    type: str
    title: str
    body: Optional[str] = None
    link: Optional[str] = None
    is_read: bool = False
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
