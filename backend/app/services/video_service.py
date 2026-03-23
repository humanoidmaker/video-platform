"""Video service."""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select, func, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.channel import Channel
from app.models.video import Video, VideoStatus, VideoVisibility
from app.models.video_file import VideoFile, VideoFileStatus, VideoResolution
from app.models.like import Like, LikeType
from app.models.comment import Comment
from app.models.tag import Tag, VideoTag
from app.models.watch_history import WatchHistory
from app.utils.slug_utils import generate_slug, generate_tag_slug


class VideoService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, video_id: int) -> Optional[Video]:
        result = await self.db.execute(select(Video).where(Video.id == video_id))
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Video]:
        result = await self.db.execute(select(Video).where(Video.slug == slug))
        return result.scalar_one_or_none()

    async def create(
        self,
        channel_id: int,
        title: str,
        description: Optional[str] = None,
        category_id: Optional[int] = None,
        visibility: str = "private",
        tags: Optional[List[str]] = None,
        is_age_restricted: bool = False,
        is_comments_disabled: bool = False,
        language: Optional[str] = None,
    ) -> Video:
        slug = generate_slug(title)
        video = Video(
            channel_id=channel_id,
            title=title,
            description=description,
            slug=slug,
            category_id=category_id,
            visibility=VideoVisibility(visibility),
            status=VideoStatus.UPLOADING,
            is_age_restricted=is_age_restricted,
            is_comments_disabled=is_comments_disabled,
            language=language,
        )
        self.db.add(video)
        await self.db.flush()

        if tags:
            await self._sync_tags(video.id, tags)

        await self.db.execute(
            update(Channel).where(Channel.id == channel_id).values(video_count=Channel.video_count + 1)
        )
        await self.db.flush()
        return video

    async def _sync_tags(self, video_id: int, tag_names: List[str]) -> None:
        """Sync tags for a video: create missing tags and update video_tags."""
        # Remove existing
        from sqlalchemy import delete
        await self.db.execute(delete(VideoTag).where(VideoTag.video_id == video_id))

        for name in tag_names[:30]:  # Max 30 tags
            name = name.strip().lower()
            if not name:
                continue
            slug = generate_tag_slug(name)
            result = await self.db.execute(select(Tag).where(Tag.slug == slug))
            tag = result.scalar_one_or_none()
            if not tag:
                tag = Tag(name=name, slug=slug, usage_count=1)
                self.db.add(tag)
                await self.db.flush()
            else:
                tag.usage_count += 1

            vt = VideoTag(video_id=video_id, tag_id=tag.id)
            self.db.add(vt)
        await self.db.flush()

    async def update(self, video_id: int, tags: Optional[List[str]] = None, **kwargs) -> Optional[Video]:
        video = await self.get_by_id(video_id)
        if not video:
            return None
        for key, value in kwargs.items():
            if hasattr(video, key) and value is not None:
                if key == "visibility":
                    value = VideoVisibility(value)
                setattr(video, key, value)
        if tags is not None:
            await self._sync_tags(video_id, tags)
        await self.db.flush()
        return video

    async def delete(self, video_id: int) -> bool:
        video = await self.get_by_id(video_id)
        if not video:
            return False
        video.status = VideoStatus.DELETED
        await self.db.execute(
            update(Channel).where(Channel.id == video.channel_id).values(
                video_count=func.greatest(Channel.video_count - 1, 0)
            )
        )
        await self.db.flush()
        return True

    async def publish(self, video_id: int) -> Optional[Video]:
        video = await self.get_by_id(video_id)
        if not video or video.status != VideoStatus.READY:
            return None
        video.visibility = VideoVisibility.PUBLIC
        video.published_at = datetime.now(timezone.utc)
        await self.db.flush()
        return video

    async def set_status(self, video_id: int, status: str) -> None:
        await self.db.execute(
            update(Video).where(Video.id == video_id).values(status=VideoStatus(status))
        )
        await self.db.flush()

    async def set_file_info(self, video_id: int, original_file_key: str, original_filename: str, file_size: int, duration: Optional[float] = None) -> None:
        await self.db.execute(
            update(Video).where(Video.id == video_id).values(
                original_file_key=original_file_key,
                original_filename=original_filename,
                original_file_size=file_size,
                duration=duration,
                status=VideoStatus.PROCESSING,
            )
        )
        await self.db.flush()

    async def increment_views(self, video_id: int) -> None:
        await self.db.execute(
            update(Video).where(Video.id == video_id).values(view_count=Video.view_count + 1)
        )
        channel_q = select(Video.channel_id).where(Video.id == video_id)
        result = await self.db.execute(channel_q)
        channel_id = result.scalar_one_or_none()
        if channel_id:
            await self.db.execute(
                update(Channel).where(Channel.id == channel_id).values(total_views=Channel.total_views + 1)
            )
        await self.db.flush()

    async def like_video(self, user_id: int, video_id: int, like_type: str) -> Like:
        existing = await self.db.execute(
            select(Like).where(Like.user_id == user_id, Like.video_id == video_id)
        )
        like = existing.scalar_one_or_none()
        lt = LikeType(like_type)
        if like:
            if like.like_type == lt:
                # Remove
                old_type = like.like_type
                await self.db.delete(like)
                if old_type == LikeType.LIKE:
                    await self.db.execute(update(Video).where(Video.id == video_id).values(like_count=func.greatest(Video.like_count - 1, 0)))
                else:
                    await self.db.execute(update(Video).where(Video.id == video_id).values(dislike_count=func.greatest(Video.dislike_count - 1, 0)))
                await self.db.flush()
                return like
            else:
                # Switch
                old_type = like.like_type
                like.like_type = lt
                if old_type == LikeType.LIKE:
                    await self.db.execute(update(Video).where(Video.id == video_id).values(like_count=func.greatest(Video.like_count - 1, 0), dislike_count=Video.dislike_count + 1))
                else:
                    await self.db.execute(update(Video).where(Video.id == video_id).values(dislike_count=func.greatest(Video.dislike_count - 1, 0), like_count=Video.like_count + 1))
                await self.db.flush()
                return like
        else:
            like = Like(user_id=user_id, video_id=video_id, like_type=lt)
            self.db.add(like)
            if lt == LikeType.LIKE:
                await self.db.execute(update(Video).where(Video.id == video_id).values(like_count=Video.like_count + 1))
            else:
                await self.db.execute(update(Video).where(Video.id == video_id).values(dislike_count=Video.dislike_count + 1))
            await self.db.flush()
            return like

    async def get_user_like(self, user_id: int, video_id: int) -> Optional[Like]:
        result = await self.db.execute(
            select(Like).where(Like.user_id == user_id, Like.video_id == video_id)
        )
        return result.scalar_one_or_none()

    async def add_comment(self, video_id: int, user_id: int, body: str, parent_id: Optional[int] = None) -> Comment:
        comment = Comment(
            video_id=video_id,
            user_id=user_id,
            body=body,
            parent_id=parent_id,
        )
        self.db.add(comment)
        await self.db.execute(
            update(Video).where(Video.id == video_id).values(comment_count=Video.comment_count + 1)
        )
        if parent_id:
            await self.db.execute(
                update(Comment).where(Comment.id == parent_id).values(reply_count=Comment.reply_count + 1)
            )
        await self.db.flush()
        return comment

    async def update_comment(self, comment_id: int, user_id: int, body: str) -> Optional[Comment]:
        result = await self.db.execute(select(Comment).where(Comment.id == comment_id))
        comment = result.scalar_one_or_none()
        if not comment or comment.user_id != user_id:
            return None
        comment.body = body
        comment.is_edited = True
        await self.db.flush()
        return comment

    async def delete_comment(self, comment_id: int, user_id: int, is_admin: bool = False) -> bool:
        result = await self.db.execute(select(Comment).where(Comment.id == comment_id))
        comment = result.scalar_one_or_none()
        if not comment:
            return False
        if not is_admin and comment.user_id != user_id:
            return False
        comment.is_deleted = True
        comment.body = "[deleted]"
        await self.db.execute(
            update(Video).where(Video.id == comment.video_id).values(
                comment_count=func.greatest(Video.comment_count - 1, 0)
            )
        )
        await self.db.flush()
        return True

    async def get_comments(self, video_id: int, parent_id: Optional[int] = None, page: int = 1, page_size: int = 20):
        conditions = [Comment.video_id == video_id, Comment.is_deleted == False]
        if parent_id is not None:
            conditions.append(Comment.parent_id == parent_id)
        else:
            conditions.append(Comment.parent_id == None)  # noqa: E711

        query = select(Comment).where(and_(*conditions))
        count_query = select(func.count()).select_from(Comment).where(and_(*conditions))
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.offset((page - 1) * page_size).limit(page_size).order_by(Comment.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def list_channel_videos(self, channel_id: int, page: int = 1, page_size: int = 20, status_filter: Optional[str] = None):
        conditions = [Video.channel_id == channel_id, Video.status != VideoStatus.DELETED]
        if status_filter:
            conditions.append(Video.status == VideoStatus(status_filter))

        query = select(Video).where(and_(*conditions))
        count_query = select(func.count()).select_from(Video).where(and_(*conditions))
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.offset((page - 1) * page_size).limit(page_size).order_by(Video.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def list_public_videos(self, page: int = 1, page_size: int = 20, category_id: Optional[int] = None):
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

    async def record_watch(self, user_id: int, video_id: int, watch_duration: float = 0, progress_percent: float = 0, last_position: float = 0) -> WatchHistory:
        result = await self.db.execute(
            select(WatchHistory).where(
                WatchHistory.user_id == user_id,
                WatchHistory.video_id == video_id,
            ).order_by(WatchHistory.watched_at.desc())
        )
        history = result.scalar_one_or_none()
        if history:
            history.watch_duration = watch_duration
            history.progress_percent = progress_percent
            history.last_position = last_position
        else:
            history = WatchHistory(
                user_id=user_id,
                video_id=video_id,
                watch_duration=watch_duration,
                progress_percent=progress_percent,
                last_position=last_position,
            )
            self.db.add(history)
        await self.db.flush()
        return history

    async def get_video_tags(self, video_id: int) -> List[Tag]:
        result = await self.db.execute(
            select(Tag).join(VideoTag, VideoTag.tag_id == Tag.id).where(VideoTag.video_id == video_id)
        )
        return list(result.scalars().all())
