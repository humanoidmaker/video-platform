"""Playlist schemas."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class PlaylistCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    visibility: str = Field(default="public", pattern="^(public|unlisted|private)$")


class PlaylistUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    visibility: Optional[str] = Field(None, pattern="^(public|unlisted|private)$")


class PlaylistItemCreate(BaseModel):
    video_id: int
    position: Optional[int] = None


class PlaylistItemReorder(BaseModel):
    item_id: int
    new_position: int


class PlaylistItemResponse(BaseModel):
    id: int
    video_id: int
    position: int
    added_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PlaylistResponse(BaseModel):
    id: int
    channel_id: int
    title: str
    description: Optional[str] = None
    slug: str
    visibility: str
    thumbnail_url: Optional[str] = None
    video_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
