"""Notification tasks."""

import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task
def notify_subscribers_new_video(channel_id: int, video_id: int, video_title: str):
    """Send notifications to all channel subscribers when a new video is published."""
    import asyncio
    from app.database import async_session_factory
    from app.models.subscription import Subscription
    from app.models.channel import Channel
    from app.services.notification_service import NotificationService
    from sqlalchemy import select

    async def run():
        async with async_session_factory() as session:
            # Get channel info
            ch_result = await session.execute(select(Channel).where(Channel.id == channel_id))
            channel = ch_result.scalar_one_or_none()
            if not channel:
                return

            # Get subscribers with notifications enabled
            sub_result = await session.execute(
                select(Subscription).where(
                    Subscription.channel_id == channel_id,
                    Subscription.notify == True,
                )
            )
            subs = sub_result.scalars().all()

            service = NotificationService(session)
            for sub in subs:
                await service.create(
                    user_id=sub.user_id,
                    notification_type="new_video",
                    title=f"{channel.name} uploaded: {video_title}",
                    body=f"New video from {channel.name}",
                    link=f"/watch/{video_id}",
                    actor_id=channel.owner_id,
                    video_id=video_id,
                    channel_id=channel_id,
                )
            await session.commit()
            logger.info(f"Sent new video notifications to {len(subs)} subscribers for video {video_id}")

    asyncio.get_event_loop().run_until_complete(run())


@celery_app.task
def notify_comment_reply(comment_id: int, replier_id: int, video_id: int):
    """Notify the parent comment author about a reply."""
    import asyncio
    from app.database import async_session_factory
    from app.models.comment import Comment
    from app.models.user import User
    from app.services.notification_service import NotificationService
    from sqlalchemy import select

    async def run():
        async with async_session_factory() as session:
            result = await session.execute(select(Comment).where(Comment.id == comment_id))
            comment = result.scalar_one_or_none()
            if not comment or not comment.parent_id:
                return

            parent_result = await session.execute(select(Comment).where(Comment.id == comment.parent_id))
            parent = parent_result.scalar_one_or_none()
            if not parent or parent.user_id == replier_id:
                return

            replier_result = await session.execute(select(User).where(User.id == replier_id))
            replier = replier_result.scalar_one_or_none()
            replier_name = replier.display_name if replier else "Someone"

            service = NotificationService(session)
            await service.create(
                user_id=parent.user_id,
                notification_type="comment_reply",
                title=f"{replier_name} replied to your comment",
                link=f"/watch/{video_id}?comment={comment_id}",
                actor_id=replier_id,
                video_id=video_id,
            )
            await session.commit()

    asyncio.get_event_loop().run_until_complete(run())


@celery_app.task
def notify_new_subscriber(channel_id: int, subscriber_id: int):
    """Notify channel owner about a new subscriber."""
    import asyncio
    from app.database import async_session_factory
    from app.models.channel import Channel
    from app.models.user import User
    from app.services.notification_service import NotificationService
    from sqlalchemy import select

    async def run():
        async with async_session_factory() as session:
            ch_result = await session.execute(select(Channel).where(Channel.id == channel_id))
            channel = ch_result.scalar_one_or_none()
            if not channel:
                return

            sub_result = await session.execute(select(User).where(User.id == subscriber_id))
            subscriber = sub_result.scalar_one_or_none()
            sub_name = subscriber.display_name if subscriber else "Someone"

            service = NotificationService(session)
            await service.create(
                user_id=channel.owner_id,
                notification_type="new_subscriber",
                title=f"{sub_name} subscribed to your channel",
                link=f"/channel/{channel.handle}",
                actor_id=subscriber_id,
                channel_id=channel_id,
            )
            await session.commit()

    asyncio.get_event_loop().run_until_complete(run())
