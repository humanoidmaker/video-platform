"""SQLAlchemy models for Video Platform."""

from app.models.user import User
from app.models.channel import Channel
from app.models.category import Category
from app.models.tag import Tag, VideoTag
from app.models.video import Video
from app.models.video_file import VideoFile
from app.models.playlist import Playlist
from app.models.playlist_item import PlaylistItem
from app.models.comment import Comment
from app.models.like import Like
from app.models.subscription import Subscription
from app.models.watch_history import WatchHistory
from app.models.notification import Notification
from app.models.report import Report
from app.models.analytics import VideoAnalytics, ChannelAnalytics, PlatformAnalytics

__all__ = [
    "User", "Channel", "Category", "Tag", "VideoTag",
    "Video", "VideoFile", "Playlist", "PlaylistItem",
    "Comment", "Like", "Subscription", "WatchHistory",
    "Notification", "Report",
    "VideoAnalytics", "ChannelAnalytics", "PlatformAnalytics",
]
