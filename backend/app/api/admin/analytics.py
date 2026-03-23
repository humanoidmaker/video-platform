"""Admin analytics routes."""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import require_admin
from app.schemas.analytics import PlatformAnalyticsResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/admin/analytics", tags=["admin-analytics"])


@router.get("/platform", response_model=list[PlatformAnalyticsResponse])
async def get_platform_analytics(
    start_date: date = None,
    end_date: date = None,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    service = AnalyticsService(db)
    data = await service.get_platform_analytics(start_date, end_date)
    return [PlatformAnalyticsResponse.model_validate(d) for d in data]


@router.get("/video/{video_id}")
async def get_video_analytics(
    video_id: int,
    start_date: date = None,
    end_date: date = None,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    service = AnalyticsService(db)
    data = await service.get_video_analytics(video_id, start_date, end_date)
    return [{"video_id": d.video_id, "date": d.date.isoformat(), "views": d.views, "watch_time_seconds": d.watch_time_seconds, "likes": d.likes, "dislikes": d.dislikes, "comments": d.comments} for d in data]


@router.get("/channel/{channel_id}")
async def get_channel_analytics(
    channel_id: int,
    start_date: date = None,
    end_date: date = None,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    service = AnalyticsService(db)
    data = await service.get_channel_analytics(channel_id, start_date, end_date)
    return [{"channel_id": d.channel_id, "date": d.date.isoformat(), "views": d.views, "new_subscribers": d.new_subscribers, "total_likes": d.total_likes} for d in data]
