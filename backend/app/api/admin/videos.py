"""Admin video moderation routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import require_admin
from app.models.video import Video, VideoStatus, VideoVisibility
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.video import VideoResponse, VideoBriefResponse
from app.services.video_service import VideoService
from app.utils.pagination import PaginatedResponse as PR

router = APIRouter(prefix="/api/admin/videos", tags=["admin-videos"])


@router.get("", response_model=PaginatedResponse)
async def list_all_videos(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: str = None,
    search: str = None,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    conditions = []
    if status_filter:
        conditions.append(Video.status == VideoStatus(status_filter))
    if search:
        conditions.append(Video.title.ilike(f"%{search}%"))

    query = select(Video)
    count_query = select(func.count()).select_from(Video)
    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))
    total = (await db.execute(count_query)).scalar() or 0
    query = query.offset((page - 1) * page_size).limit(page_size).order_by(Video.created_at.desc())
    result = await db.execute(query)
    videos = result.scalars().all()
    return PR.create([VideoBriefResponse.model_validate(v) for v in videos], total, page, page_size)


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(video_id: int, current_user: dict = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    service = VideoService(db)
    video = await service.get_by_id(video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    return video


@router.post("/{video_id}/takedown", response_model=MessageResponse)
async def takedown_video(video_id: int, current_user: dict = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    service = VideoService(db)
    video = await service.get_by_id(video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    await service.delete(video_id)
    return MessageResponse(message="Video taken down")


@router.post("/{video_id}/restore", response_model=MessageResponse)
async def restore_video(video_id: int, current_user: dict = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    service = VideoService(db)
    video = await service.get_by_id(video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    await service.set_status(video_id, "ready")
    return MessageResponse(message="Video restored")


@router.post("/{video_id}/set-visibility", response_model=MessageResponse)
async def set_visibility(video_id: int, visibility: str = Query(pattern="^(public|unlisted|private)$"), current_user: dict = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    service = VideoService(db)
    video = await service.get_by_id(video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    await service.update(video_id, visibility=visibility)
    return MessageResponse(message=f"Visibility set to {visibility}")
