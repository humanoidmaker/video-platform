"""Channel service."""

from typing import Optional

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.channel import Channel
from app.models.subscription import Subscription
from app.models.user import User, UserRole


class ChannelService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, channel_id: int) -> Optional[Channel]:
        result = await self.db.execute(select(Channel).where(Channel.id == channel_id))
        return result.scalar_one_or_none()

    async def get_by_handle(self, handle: str) -> Optional[Channel]:
        result = await self.db.execute(select(Channel).where(Channel.handle == handle.lower()))
        return result.scalar_one_or_none()

    async def get_by_owner(self, owner_id: int) -> Optional[Channel]:
        result = await self.db.execute(select(Channel).where(Channel.owner_id == owner_id))
        return result.scalar_one_or_none()

    async def create(self, owner_id: int, handle: str, name: str, description: Optional[str] = None) -> Channel:
        existing = await self.get_by_handle(handle)
        if existing:
            raise ValueError("Handle already taken")
        channel = Channel(
            owner_id=owner_id,
            handle=handle.lower(),
            name=name,
            description=description,
        )
        self.db.add(channel)
        await self.db.flush()
        # Upgrade user role to creator if still viewer
        result = await self.db.execute(select(User).where(User.id == owner_id))
        user = result.scalar_one_or_none()
        if user and user.role == UserRole.VIEWER:
            user.role = UserRole.CREATOR
            await self.db.flush()
        return channel

    async def update(self, channel_id: int, **kwargs) -> Optional[Channel]:
        channel = await self.get_by_id(channel_id)
        if not channel:
            return None
        for key, value in kwargs.items():
            if hasattr(channel, key) and value is not None:
                setattr(channel, key, value)
        await self.db.flush()
        return channel

    async def delete(self, channel_id: int) -> bool:
        channel = await self.get_by_id(channel_id)
        if not channel:
            return False
        await self.db.delete(channel)
        await self.db.flush()
        return True

    async def subscribe(self, user_id: int, channel_id: int) -> Subscription:
        existing = await self.db.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.channel_id == channel_id,
            )
        )
        sub = existing.scalar_one_or_none()
        if sub:
            raise ValueError("Already subscribed")
        sub = Subscription(user_id=user_id, channel_id=channel_id)
        self.db.add(sub)
        await self.db.execute(
            update(Channel).where(Channel.id == channel_id).values(subscriber_count=Channel.subscriber_count + 1)
        )
        await self.db.flush()
        return sub

    async def unsubscribe(self, user_id: int, channel_id: int) -> bool:
        result = await self.db.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.channel_id == channel_id,
            )
        )
        sub = result.scalar_one_or_none()
        if not sub:
            return False
        await self.db.delete(sub)
        await self.db.execute(
            update(Channel).where(Channel.id == channel_id).values(
                subscriber_count=func.greatest(Channel.subscriber_count - 1, 0)
            )
        )
        await self.db.flush()
        return True

    async def is_subscribed(self, user_id: int, channel_id: int) -> bool:
        result = await self.db.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.channel_id == channel_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_subscribers(self, channel_id: int, page: int = 1, page_size: int = 20):
        query = select(Subscription).where(Subscription.channel_id == channel_id)
        count_query = select(func.count()).select_from(Subscription).where(Subscription.channel_id == channel_id)
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.offset((page - 1) * page_size).limit(page_size).order_by(Subscription.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def list_channels(self, page: int = 1, page_size: int = 20, search: Optional[str] = None):
        query = select(Channel).where(Channel.is_active == True)
        count_query = select(func.count()).select_from(Channel).where(Channel.is_active == True)
        if search:
            search_filter = Channel.name.ilike(f"%{search}%") | Channel.handle.ilike(f"%{search}%")
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.offset((page - 1) * page_size).limit(page_size).order_by(Channel.subscriber_count.desc())
        result = await self.db.execute(query)
        return result.scalars().all(), total
