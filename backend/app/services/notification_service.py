"""Notification service."""

from typing import Optional

from sqlalchemy import select, func, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationType


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: int,
        notification_type: str,
        title: str,
        body: Optional[str] = None,
        link: Optional[str] = None,
        actor_id: Optional[int] = None,
        video_id: Optional[int] = None,
        channel_id: Optional[int] = None,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            type=NotificationType(notification_type),
            title=title,
            body=body,
            link=link,
            actor_id=actor_id,
            video_id=video_id,
            channel_id=channel_id,
        )
        self.db.add(notification)
        await self.db.flush()
        return notification

    async def get_user_notifications(self, user_id: int, page: int = 1, page_size: int = 20, unread_only: bool = False):
        conditions = [Notification.user_id == user_id]
        if unread_only:
            conditions.append(Notification.is_read == False)

        query = select(Notification).where(and_(*conditions))
        count_query = select(func.count()).select_from(Notification).where(and_(*conditions))
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.offset((page - 1) * page_size).limit(page_size).order_by(Notification.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        result = await self.db.execute(
            select(Notification).where(Notification.id == notification_id, Notification.user_id == user_id)
        )
        notification = result.scalar_one_or_none()
        if not notification:
            return False
        notification.is_read = True
        await self.db.flush()
        return True

    async def mark_all_as_read(self, user_id: int) -> int:
        result = await self.db.execute(
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read == False)
            .values(is_read=True)
        )
        await self.db.flush()
        return result.rowcount

    async def get_unread_count(self, user_id: int) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user_id, Notification.is_read == False)
        )
        return result.scalar() or 0

    async def delete(self, notification_id: int, user_id: int) -> bool:
        result = await self.db.execute(
            select(Notification).where(Notification.id == notification_id, Notification.user_id == user_id)
        )
        notification = result.scalar_one_or_none()
        if not notification:
            return False
        await self.db.delete(notification)
        await self.db.flush()
        return True
