"""Channel schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ChannelCreate(BaseModel):
    handle: str = Field(min_length=3, max_length=50, pattern="^[a-zA-Z0-9_-]+$")
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None


class ChannelUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class ChannelResponse(BaseModel):
    id: int
    owner_id: int
    handle: str
    name: str
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None
    subscriber_count: int = 0
    video_count: int = 0
    total_views: int = 0
    is_verified: bool = False
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ChannelBriefResponse(BaseModel):
    id: int
    handle: str
    name: str
    avatar_url: Optional[str] = None
    subscriber_count: int = 0
    is_verified: bool = False

    model_config = {"from_attributes": True}
