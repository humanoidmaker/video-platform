"""Cleanup tasks for purging old data."""

import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task
def cleanup():
    """Clean up old read notifications."""
    import asyncio
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import delete
    from app.database import async_session_factory
    from app.models.notification import Notification

    async def run():
        async with async_session_factory() as session:
            cutoff = datetime.now(timezone.utc) - timedelta(days=90)
            result = await session.execute(
                delete(Notification).where(Notification.created_at < cutoff, Notification.is_read == True)
            )
            logger.info(f"Cleaned up {result.rowcount} old notifications")
            await session.commit()

    asyncio.get_event_loop().run_until_complete(run())


@celery_app.task
def cleanup_failed_uploads():
    """Clean up videos stuck in uploading/processing state for more than 24 hours."""
    import asyncio
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import update
    from app.database import async_session_factory
    from app.models.video import Video, VideoStatus

    async def run():
        async with async_session_factory() as session:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
            result = await session.execute(
                update(Video)
                .where(
                    Video.status.in_([VideoStatus.UPLOADING, VideoStatus.PROCESSING]),
                    Video.created_at < cutoff,
                )
                .values(status=VideoStatus.FAILED)
            )
            logger.info(f"Marked {result.rowcount} stale uploads as failed")
            await session.commit()

    asyncio.get_event_loop().run_until_complete(run())
