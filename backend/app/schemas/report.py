"""Report schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ReportCreate(BaseModel):
    target_type: str = Field(pattern="^(video|comment|channel)$")
    target_id: int
    reason: str = Field(pattern="^(spam|harassment|hate_speech|violence|nudity|misinformation|copyright|other)$")
    description: Optional[str] = Field(None, max_length=2000)


class ReportResolve(BaseModel):
    resolution_note: Optional[str] = Field(None, max_length=2000)
    status: str = Field(pattern="^(resolved|dismissed)$")


class ReportResponse(BaseModel):
    id: int
    reporter_id: int
    target_type: str
    target_id: int
    reason: str
    description: Optional[str] = None
    status: str
    resolution_note: Optional[str] = None
    resolved_by: Optional[int] = None
    resolved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
