"""Video model."""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class VideoStatus(str, enum.Enum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    DELETED = "deleted"


class VideoVisibility(str, enum.Enum):
    PUBLIC = "public"
    UNLISTED = "unlisted"
    PRIVATE = "private"


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    slug: Mapped[str] = mapped_column(String(250), unique=True, nullable=False, index=True)
    status: Mapped[VideoStatus] = mapped_column(Enum(VideoStatus), default=VideoStatus.UPLOADING, nullable=False, index=True)
    visibility: Mapped[VideoVisibility] = mapped_column(Enum(VideoVisibility), default=VideoVisibility.PRIVATE, nullable=False, index=True)
    duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    original_filename: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    original_file_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    original_file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    thumbnail_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    dislike_count: Mapped[int] = mapped_column(Integer, default=0)
    comment_count: Mapped[int] = mapped_column(Integer, default=0)
    is_age_restricted: Mapped[bool] = mapped_column(Boolean, default=False)
    is_comments_disabled: Mapped[bool] = mapped_column(Boolean, default=False)
    allow_embedding: Mapped[bool] = mapped_column(Boolean, default=True)
    language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    channel: Mapped["Channel"] = relationship("Channel", back_populates="videos", lazy="selectin")  # noqa: F821
    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="videos", lazy="selectin")  # noqa: F821
    video_files: Mapped[list["VideoFile"]] = relationship("VideoFile", back_populates="video", lazy="selectin")  # noqa: F821
    comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="video", lazy="noload")  # noqa: F821
    likes: Mapped[list["Like"]] = relationship("Like", back_populates="video", lazy="noload")  # noqa: F821
