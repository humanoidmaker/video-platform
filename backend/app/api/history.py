"""Watch history API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.watch_history import WatchHistory
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.history import WatchHistoryUpdate, WatchHistoryResponse
from app.services.video_service import VideoService
from app.utils.pagination import PaginatedResponse as PR

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("", response_model=PaginatedResponse)
async def get_watch_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user["user_id"]
    conditions = [WatchHistory.user_id == user_id]
    query = select(WatchHistory).where(and_(*conditions))
    count_query = select(func.count()).select_from(WatchHistory).where(and_(*conditions))
    total = (await db.execute(count_query)).scalar() or 0
    query = query.offset((page - 1) * page_size).limit(page_size).order_by(WatchHistory.watched_at.desc())
    result = await db.execute(query)
    items = result.scalars().all()
    return PR.create([WatchHistoryResponse.model_validate(h) for h in items], total, page, page_size)


@router.post("/{video_id}", response_model=WatchHistoryResponse)
async def update_watch_progress(
    video_id: int,
    data: WatchHistoryUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = VideoService(db)
    video = await service.get_by_id(video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    history = await service.record_watch(
        current_user["user_id"], video_id,
        data.watch_duration, data.progress_percent, data.last_position,
    )
    return history


@router.delete("", response_model=MessageResponse)
async def clear_watch_history(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await db.execute(delete(WatchHistory).where(WatchHistory.user_id == current_user["user_id"]))
    await db.flush()
    return MessageResponse(message="Watch history cleared")


@router.delete("/{video_id}", response_model=MessageResponse)
async def remove_from_history(video_id: int, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        delete(WatchHistory).where(
            WatchHistory.user_id == current_user["user_id"],
            WatchHistory.video_id == video_id,
        )
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not in history")
    await db.flush()
    return MessageResponse(message="Removed from history")
