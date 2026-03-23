"""Search API routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.video import VideoBriefResponse
from app.schemas.channel import ChannelBriefResponse
from app.schemas.playlist import PlaylistResponse
from app.services.search_service import SearchService
from app.utils.pagination import PaginatedResponse as PR

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("", response_model=PaginatedResponse)
async def search(
    q: str = Query(min_length=1, max_length=200),
    type: str = Query(default="video", pattern="^(video|channel|playlist)$"),
    category_id: int = None,
    sort_by: str = Query(default="relevance", pattern="^(relevance|date|views|rating)$"),
    duration_filter: str = None,
    upload_date: str = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    service = SearchService(db)

    if type == "channel":
        channels, total = await service.search_channels(q, page, page_size)
        return PR.create([ChannelBriefResponse.model_validate(c) for c in channels], total, page, page_size)
    elif type == "playlist":
        playlists, total = await service.search_playlists(q, page, page_size)
        return PR.create([PlaylistResponse.model_validate(p) for p in playlists], total, page, page_size)
    else:
        videos, total = await service.search_videos(q, category_id, sort_by, duration_filter, upload_date, page, page_size)
        return PR.create([VideoBriefResponse.model_validate(v) for v in videos], total, page, page_size)
