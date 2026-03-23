"""Permission checking utilities."""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.models.channel import Channel
from app.models.video import Video


async def check_channel_owner(db: AsyncSession, user_id: int, channel_id: int) -> Channel:
    """Check if user owns the channel."""
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")
    if channel.owner_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this channel")
    return channel


async def check_video_owner(db: AsyncSession, user_id: int, video_id: int) -> Video:
    """Check if user owns the video (via channel ownership)."""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    await check_channel_owner(db, user_id, video.channel_id)
    return video


async def get_user_channel(db: AsyncSession, user_id: int) -> Channel:
    """Get the channel owned by user, raising 404 if none."""
    result = await db.execute(select(Channel).where(Channel.owner_id == user_id))
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You must create a channel first")
    return channel


def check_admin(user: dict) -> None:
    """Check if user is admin or superadmin."""
    if user.get("role") not in ("admin", "superadmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
