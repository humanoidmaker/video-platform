"""Thumbnail generation tasks."""

import logging
import os
import tempfile

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def generate_video_thumbnail(self, video_id: int):
    """Generate a thumbnail from the video and upload it."""
    import asyncio
    from app.database import async_session_factory
    from app.models.video import Video
    from app.services.transcoding_service import generate_thumbnail
    from app.utils.minio_client import download_file, upload_file, get_presigned_url
    from app.config import settings
    from sqlalchemy import select, update

    async def run():
        async with async_session_factory() as session:
            result = await session.execute(select(Video).where(Video.id == video_id))
            video = result.scalar_one_or_none()
            if not video or not video.original_file_key:
                logger.error(f"Video {video_id} not found or has no original file")
                return

            if video.thumbnail_key:
                logger.info(f"Video {video_id} already has a thumbnail, skipping")
                return

            with tempfile.TemporaryDirectory() as tmpdir:
                input_path = os.path.join(tmpdir, "original")
                try:
                    data = download_file(settings.MINIO_BUCKET_VIDEOS, video.original_file_key)
                    with open(input_path, "wb") as f:
                        f.write(data)
                except Exception as e:
                    logger.error(f"Failed to download original for thumbnail: {e}")
                    return

                thumb_path = os.path.join(tmpdir, "thumbnail.jpg")
                time_offset = (video.duration or 2.0) * 0.1
                success = generate_thumbnail(input_path, thumb_path, time_offset=max(time_offset, 1.0))

                if success and os.path.exists(thumb_path):
                    thumb_key = f"thumbnails/{video_id}/auto.jpg"
                    with open(thumb_path, "rb") as f:
                        upload_file(settings.MINIO_BUCKET_THUMBNAILS, thumb_key, f.read(), "image/jpeg")

                    thumb_url = get_presigned_url(settings.MINIO_BUCKET_THUMBNAILS, thumb_key)
                    await session.execute(
                        update(Video).where(Video.id == video_id).values(
                            thumbnail_key=thumb_key,
                            thumbnail_url=thumb_url,
                        )
                    )
                    await session.commit()
                    logger.info(f"Thumbnail generated for video {video_id}")
                else:
                    logger.error(f"Thumbnail generation failed for video {video_id}")

    try:
        asyncio.get_event_loop().run_until_complete(run())
    except Exception as exc:
        logger.error(f"Thumbnail task failed for {video_id}: {exc}")
        raise self.retry(exc=exc)
