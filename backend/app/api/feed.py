"""Feed API routes — home, trending, subscriptions."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.schemas.common import PaginatedResponse
from app.schemas.video import VideoBriefResponse
from app.services.feed_service import FeedService
from app.utils.pagination import PaginatedResponse as PR

router = APIRouter(prefix="/api/feed", tags=["feed"])


@router.get("/home", response_model=PaginatedResponse)
async def home_feed(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    category_id: int = None,
    db: AsyncSession = Depends(get_db),
):
    service = FeedService(db)
    videos, total = await service.get_home_feed(page, page_size, category_id)
    return PR.create([VideoBriefResponse.model_validate(v) for v in videos], total, page, page_size)


@router.get("/trending", response_model=PaginatedResponse)
async def trending_feed(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    service = FeedService(db)
    videos, total = await service.get_trending_feed(page, page_size)
    return PR.create([VideoBriefResponse.model_validate(v) for v in videos], total, page, page_size)


@router.get("/subscriptions", response_model=PaginatedResponse)
async def subscription_feed(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = FeedService(db)
    videos, total = await service.get_subscription_feed(current_user["user_id"], page, page_size)
    return PR.create([VideoBriefResponse.model_validate(v) for v in videos], total, page, page_size)
