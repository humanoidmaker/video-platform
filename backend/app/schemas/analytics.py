"""Analytics schemas."""

from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel


class VideoAnalyticsResponse(BaseModel):
    video_id: int
    date: date
    views: int = 0
    unique_viewers: int = 0
    watch_time_seconds: float = 0.0
    avg_watch_duration: float = 0.0
    avg_completion_rate: float = 0.0
    likes: int = 0
    dislikes: int = 0
    comments: int = 0

    model_config = {"from_attributes": True}


class ChannelAnalyticsResponse(BaseModel):
    channel_id: int
    date: date
    views: int = 0
    watch_time_seconds: float = 0.0
    new_subscribers: int = 0
    lost_subscribers: int = 0
    new_videos: int = 0
    total_likes: int = 0
    total_comments: int = 0

    model_config = {"from_attributes": True}


class ChannelAnalyticsSummary(BaseModel):
    total_views: int = 0
    total_watch_time: float = 0.0
    total_subscribers: int = 0
    total_videos: int = 0
    subscriber_growth: int = 0
    view_growth_percent: float = 0.0
    daily: List[ChannelAnalyticsResponse] = []


class PlatformAnalyticsResponse(BaseModel):
    date: date
    total_users: int = 0
    new_users: int = 0
    active_users: int = 0
    total_videos: int = 0
    new_videos: int = 0
    total_views: int = 0
    total_watch_time: float = 0.0
    total_channels: int = 0
    new_channels: int = 0
    storage_used_bytes: Optional[int] = None

    model_config = {"from_attributes": True}


class DashboardStats(BaseModel):
    total_users: int = 0
    total_channels: int = 0
    total_videos: int = 0
    total_views: int = 0
    new_users_today: int = 0
    new_videos_today: int = 0
    pending_reports: int = 0
    active_users_today: int = 0
