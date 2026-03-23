"""Feed service — home, trending, subscription feeds."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.video import Video, VideoStatus, VideoVisibility
from app.models.subscription import Subscription


class FeedService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_home_feed(self, page: int = 1, page_size: int = 20, category_id: Optional[int] = None):
        """Home feed: recent public videos, optionally filtered by category."""
        conditions = [
            Video.status == VideoStatus.READY,
            Video.visibility == VideoVisibility.PUBLIC,
        ]
        if category_id:
            conditions.append(Video.category_id == category_id)

        query = select(Video).where(and_(*conditions))
        count_query = select(func.count()).select_from(Video).where(and_(*conditions))
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.offset((page - 1) * page_size).limit(page_size).order_by(Video.published_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def get_trending_feed(self, page: int = 1, page_size: int = 20):
        """Trending feed: most viewed public videos in the last N hours."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=settings.TRENDING_WINDOW_HOURS)
        conditions = [
            Video.status == VideoStatus.READY,
            Video.visibility == VideoVisibility.PUBLIC,
            Video.published_at >= cutoff,
        ]

        query = select(Video).where(and_(*conditions))
        count_query = select(func.count()).select_from(Video).where(and_(*conditions))
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.offset((page - 1) * page_size).limit(page_size).order_by(Video.view_count.desc())
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def get_subscription_feed(self, user_id: int, page: int = 1, page_size: int = 20):
        """Subscription feed: latest videos from subscribed channels."""
        sub_query = select(Subscription.channel_id).where(Subscription.user_id == user_id)

        conditions = [
            Video.status == VideoStatus.READY,
            Video.visibility == VideoVisibility.PUBLIC,
            Video.channel_id.in_(sub_query),
        ]

        query = select(Video).where(and_(*conditions))
        count_query = select(func.count()).select_from(Video).where(and_(*conditions))
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.offset((page - 1) * page_size).limit(page_size).order_by(Video.published_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all(), total
