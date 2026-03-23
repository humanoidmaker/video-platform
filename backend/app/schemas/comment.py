"""Comment schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)
    parent_id: Optional[int] = None


class CommentUpdate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)


class CommentResponse(BaseModel):
    id: int
    video_id: int
    user_id: int
    parent_id: Optional[int] = None
    body: str
    like_count: int = 0
    reply_count: int = 0
    is_pinned: bool = False
    is_edited: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
