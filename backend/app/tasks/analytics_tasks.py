"""Analytics aggregation tasks."""

import logging
from datetime import date, timedelta

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task
def aggregate_daily_stats():
    """Aggregate daily analytics for videos and platform."""
    import asyncio
    from app.database import async_session_factory
    from app.services.analytics_service import AnalyticsService

    async def run():
        yesterday = date.today() - timedelta(days=1)
        async with async_session_factory() as session:
            service = AnalyticsService(session)
            await service.aggregate_daily_video_analytics(yesterday)
            await service.aggregate_daily_platform_analytics(yesterday)
            await session.commit()
            logger.info(f"Daily analytics aggregated for {yesterday}")

    asyncio.get_event_loop().run_until_complete(run())
