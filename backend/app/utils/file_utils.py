"""File handling utilities."""

import secrets
from typing import List

from fastapi import HTTPException, UploadFile, status

from app.config import settings


def validate_video_upload(file: UploadFile) -> None:
    """Validate an uploaded video file."""
    if file.content_type not in settings.ALLOWED_VIDEO_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid video type: {file.content_type}. Allowed: {settings.ALLOWED_VIDEO_TYPES}",
        )
    if file.size and file.size > settings.MAX_VIDEO_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Video file too large. Maximum size: {settings.MAX_VIDEO_SIZE_MB}MB",
        )


def validate_image_upload(file: UploadFile, max_size_mb: int = 10) -> None:
    """Validate an uploaded image file."""
    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image type: {file.content_type}. Allowed: {settings.ALLOWED_IMAGE_TYPES}",
        )
    if file.size and file.size > max_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image file too large. Maximum size: {max_size_mb}MB",
        )


def generate_file_key(prefix: str, filename: str) -> str:
    """Generate a unique file key for storage."""
    suffix = secrets.token_hex(8)
    ext = filename.rsplit(".", 1)[-1] if "." in filename else "bin"
    return f"{prefix}/{suffix}.{ext}"
