"""Video schemas."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class VideoCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    category_id: Optional[int] = None
    visibility: str = Field(default="private", pattern="^(public|unlisted|private)$")
    tags: List[str] = Field(default_factory=list)
    is_age_restricted: bool = False
    is_comments_disabled: bool = False
    language: Optional[str] = None


class VideoUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category_id: Optional[int] = None
    visibility: Optional[str] = Field(None, pattern="^(public|unlisted|private)$")
    tags: Optional[List[str]] = None
    is_age_restricted: Optional[bool] = None
    is_comments_disabled: Optional[bool] = None
    language: Optional[str] = None


class VideoFileResponse(BaseModel):
    id: int
    resolution: str
    status: str
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    bitrate: Optional[int] = None
    codec: Optional[str] = None

    model_config = {"from_attributes": True}


class VideoResponse(BaseModel):
    id: int
    channel_id: int
    category_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    slug: str
    status: str
    visibility: str
    duration: Optional[float] = None
    thumbnail_url: Optional[str] = None
    view_count: int = 0
    like_count: int = 0
    dislike_count: int = 0
    comment_count: int = 0
    is_age_restricted: bool = False
    is_comments_disabled: bool = False
    allow_embedding: bool = True
    language: Optional[str] = None
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    video_files: List[VideoFileResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class VideoBriefResponse(BaseModel):
    id: int
    channel_id: int
    title: str
    slug: str
    status: str
    visibility: str
    duration: Optional[float] = None
    thumbnail_url: Optional[str] = None
    view_count: int = 0
    like_count: int = 0
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
