"""Analytics service."""

from datetime import date, datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import VideoAnalytics, ChannelAnalytics, PlatformAnalytics
from app.models.video import Video, VideoStatus
from app.models.channel import Channel
from app.models.user import User
from app.models.watch_history import WatchHistory
from app.models.subscription import Subscription
from app.models.like import Like, LikeType
from app.models.comment import Comment
from app.models.report import Report, ReportStatus


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_video_analytics(self, video_id: int, start_date: date, end_date: date) -> List[VideoAnalytics]:
        result = await self.db.execute(
            select(VideoAnalytics).where(
                VideoAnalytics.video_id == video_id,
                VideoAnalytics.date >= start_date,
                VideoAnalytics.date <= end_date,
            ).order_by(VideoAnalytics.date.asc())
        )
        return list(result.scalars().all())

    async def get_channel_analytics(self, channel_id: int, start_date: date, end_date: date) -> List[ChannelAnalytics]:
        result = await self.db.execute(
            select(ChannelAnalytics).where(
                ChannelAnalytics.channel_id == channel_id,
                ChannelAnalytics.date >= start_date,
                ChannelAnalytics.date <= end_date,
            ).order_by(ChannelAnalytics.date.asc())
        )
        return list(result.scalars().all())

    async def get_platform_analytics(self, start_date: date, end_date: date) -> List[PlatformAnalytics]:
        result = await self.db.execute(
            select(PlatformAnalytics).where(
                PlatformAnalytics.date >= start_date,
                PlatformAnalytics.date <= end_date,
            ).order_by(PlatformAnalytics.date.asc())
        )
        return list(result.scalars().all())

    async def get_dashboard_stats(self) -> dict:
        today = datetime.now(timezone.utc).date()
        today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)

        total_users = (await self.db.execute(select(func.count()).select_from(User))).scalar() or 0
        total_channels = (await self.db.execute(select(func.count()).select_from(Channel))).scalar() or 0
        total_videos = (await self.db.execute(
            select(func.count()).select_from(Video).where(Video.status != VideoStatus.DELETED)
        )).scalar() or 0
        total_views = (await self.db.execute(
            select(func.coalesce(func.sum(Video.view_count), 0)).select_from(Video)
        )).scalar() or 0
        new_users_today = (await self.db.execute(
            select(func.count()).select_from(User).where(User.created_at >= today_start)
        )).scalar() or 0
        new_videos_today = (await self.db.execute(
            select(func.count()).select_from(Video).where(Video.created_at >= today_start)
        )).scalar() or 0
        pending_reports = (await self.db.execute(
            select(func.count()).select_from(Report).where(Report.status == ReportStatus.PENDING)
        )).scalar() or 0
        active_users_today = (await self.db.execute(
            select(func.count(func.distinct(WatchHistory.user_id))).select_from(WatchHistory).where(WatchHistory.watched_at >= today_start)
        )).scalar() or 0

        return {
            "total_users": total_users,
            "total_channels": total_channels,
            "total_videos": total_videos,
            "total_views": total_views,
            "new_users_today": new_users_today,
            "new_videos_today": new_videos_today,
            "pending_reports": pending_reports,
            "active_users_today": active_users_today,
        }

    async def aggregate_daily_video_analytics(self, target_date: date) -> None:
        """Aggregate daily analytics for all videos."""
        day_start = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)

        # Get all videos that had activity
        video_ids_result = await self.db.execute(
            select(func.distinct(WatchHistory.video_id)).where(
                WatchHistory.watched_at >= day_start,
                WatchHistory.watched_at < day_end,
            )
        )
        video_ids = list(video_ids_result.scalars().all())

        for video_id in video_ids:
            views = (await self.db.execute(
                select(func.count()).select_from(WatchHistory).where(
                    WatchHistory.video_id == video_id,
                    WatchHistory.watched_at >= day_start,
                    WatchHistory.watched_at < day_end,
                )
            )).scalar() or 0

            unique_viewers = (await self.db.execute(
                select(func.count(func.distinct(WatchHistory.user_id))).select_from(WatchHistory).where(
                    WatchHistory.video_id == video_id,
                    WatchHistory.watched_at >= day_start,
                    WatchHistory.watched_at < day_end,
                )
            )).scalar() or 0

            watch_time = (await self.db.execute(
                select(func.coalesce(func.sum(WatchHistory.watch_duration), 0)).select_from(WatchHistory).where(
                    WatchHistory.video_id == video_id,
                    WatchHistory.watched_at >= day_start,
                    WatchHistory.watched_at < day_end,
                )
            )).scalar() or 0

            likes = (await self.db.execute(
                select(func.count()).select_from(Like).where(
                    Like.video_id == video_id,
                    Like.like_type == LikeType.LIKE,
                    Like.created_at >= day_start,
                    Like.created_at < day_end,
                )
            )).scalar() or 0

            dislikes = (await self.db.execute(
                select(func.count()).select_from(Like).where(
                    Like.video_id == video_id,
                    Like.like_type == LikeType.DISLIKE,
                    Like.created_at >= day_start,
                    Like.created_at < day_end,
                )
            )).scalar() or 0

            comments = (await self.db.execute(
                select(func.count()).select_from(Comment).where(
                    Comment.video_id == video_id,
                    Comment.created_at >= day_start,
                    Comment.created_at < day_end,
                )
            )).scalar() or 0

            analytics = VideoAnalytics(
                video_id=video_id,
                date=target_date,
                views=views,
                unique_viewers=unique_viewers,
                watch_time_seconds=float(watch_time),
                avg_watch_duration=float(watch_time) / views if views > 0 else 0,
                likes=likes,
                dislikes=dislikes,
                comments=comments,
            )
            self.db.add(analytics)

        await self.db.flush()

    async def aggregate_daily_platform_analytics(self, target_date: date) -> None:
        """Aggregate daily platform-wide analytics."""
        day_start = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)

        total_users = (await self.db.execute(select(func.count()).select_from(User))).scalar() or 0
        new_users = (await self.db.execute(
            select(func.count()).select_from(User).where(User.created_at >= day_start, User.created_at < day_end)
        )).scalar() or 0
        active_users = (await self.db.execute(
            select(func.count(func.distinct(WatchHistory.user_id))).select_from(WatchHistory).where(
                WatchHistory.watched_at >= day_start, WatchHistory.watched_at < day_end
            )
        )).scalar() or 0
        total_videos = (await self.db.execute(
            select(func.count()).select_from(Video).where(Video.status != VideoStatus.DELETED)
        )).scalar() or 0
        new_videos = (await self.db.execute(
            select(func.count()).select_from(Video).where(Video.created_at >= day_start, Video.created_at < day_end)
        )).scalar() or 0
        total_views = (await self.db.execute(
            select(func.count()).select_from(WatchHistory).where(
                WatchHistory.watched_at >= day_start, WatchHistory.watched_at < day_end
            )
        )).scalar() or 0
        total_watch_time = (await self.db.execute(
            select(func.coalesce(func.sum(WatchHistory.watch_duration), 0)).select_from(WatchHistory).where(
                WatchHistory.watched_at >= day_start, WatchHistory.watched_at < day_end
            )
        )).scalar() or 0
        total_channels = (await self.db.execute(select(func.count()).select_from(Channel))).scalar() or 0
        new_channels = (await self.db.execute(
            select(func.count()).select_from(Channel).where(Channel.created_at >= day_start, Channel.created_at < day_end)
        )).scalar() or 0

        pa = PlatformAnalytics(
            date=target_date,
            total_users=total_users,
            new_users=new_users,
            active_users=active_users,
            total_videos=total_videos,
            new_videos=new_videos,
            total_views=total_views,
            total_watch_time=float(total_watch_time),
            total_channels=total_channels,
            new_channels=new_channels,
        )
        self.db.add(pa)
        await self.db.flush()
