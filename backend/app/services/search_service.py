"""Search service."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.video import Video, VideoStatus, VideoVisibility
from app.models.channel import Channel
from app.models.playlist import Playlist, PlaylistVisibility


class SearchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_videos(
        self,
        query: str,
        category_id: Optional[int] = None,
        sort_by: str = "relevance",
        duration_filter: Optional[str] = None,
        upload_date: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ):
        conditions = [
            Video.status == VideoStatus.READY,
            Video.visibility == VideoVisibility.PUBLIC,
            or_(
                Video.title.ilike(f"%{query}%"),
                Video.description.ilike(f"%{query}%"),
            ),
        ]

        if category_id:
            conditions.append(Video.category_id == category_id)

        if duration_filter:
            if duration_filter == "short":
                conditions.append(Video.duration < 240)
            elif duration_filter == "medium":
                conditions.append(and_(Video.duration >= 240, Video.duration < 1200))
            elif duration_filter == "long":
                conditions.append(Video.duration >= 1200)

        if upload_date:
            now = datetime.now(timezone.utc)
            if upload_date == "today":
                conditions.append(Video.published_at >= now - timedelta(days=1))
            elif upload_date == "week":
                conditions.append(Video.published_at >= now - timedelta(weeks=1))
            elif upload_date == "month":
                conditions.append(Video.published_at >= now - timedelta(days=30))
            elif upload_date == "year":
                conditions.append(Video.published_at >= now - timedelta(days=365))

        base_query = select(Video).where(and_(*conditions))
        count_query = select(func.count()).select_from(Video).where(and_(*conditions))
        total = (await self.db.execute(count_query)).scalar() or 0

        if sort_by == "date":
            base_query = base_query.order_by(Video.published_at.desc())
        elif sort_by == "views":
            base_query = base_query.order_by(Video.view_count.desc())
        elif sort_by == "rating":
            base_query = base_query.order_by(Video.like_count.desc())
        else:  # relevance
            base_query = base_query.order_by(Video.view_count.desc(), Video.published_at.desc())

        base_query = base_query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(base_query)
        return result.scalars().all(), total

    async def search_channels(self, query: str, page: int = 1, page_size: int = 20):
        conditions = [
            Channel.is_active == True,
            or_(
                Channel.name.ilike(f"%{query}%"),
                Channel.handle.ilike(f"%{query}%"),
                Channel.description.ilike(f"%{query}%"),
            ),
        ]

        base_query = select(Channel).where(and_(*conditions))
        count_query = select(func.count()).select_from(Channel).where(and_(*conditions))
        total = (await self.db.execute(count_query)).scalar() or 0
        base_query = base_query.offset((page - 1) * page_size).limit(page_size).order_by(Channel.subscriber_count.desc())
        result = await self.db.execute(base_query)
        return result.scalars().all(), total

    async def search_playlists(self, query: str, page: int = 1, page_size: int = 20):
        conditions = [
            Playlist.visibility == PlaylistVisibility.PUBLIC,
            or_(
                Playlist.title.ilike(f"%{query}%"),
                Playlist.description.ilike(f"%{query}%"),
            ),
        ]

        base_query = select(Playlist).where(and_(*conditions))
        count_query = select(func.count()).select_from(Playlist).where(and_(*conditions))
        total = (await self.db.execute(count_query)).scalar() or 0
        base_query = base_query.offset((page - 1) * page_size).limit(page_size).order_by(Playlist.video_count.desc())
        result = await self.db.execute(base_query)
        return result.scalars().all(), total
