"""Video transcoding tasks."""

import logging
import os
import tempfile

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def process_video(self, video_id: int):
    """Download original video, transcode to multiple resolutions, upload results."""
    import asyncio
    from app.database import async_session_factory
    from app.models.video import Video, VideoStatus
    from app.models.video_file import VideoFile, VideoFileStatus, VideoResolution
    from app.services.transcoding_service import (
        probe_video, get_video_duration, get_video_resolution,
        get_target_resolutions, transcode_video,
    )
    from app.utils.minio_client import download_file, upload_file, get_presigned_url
    from app.config import settings
    from sqlalchemy import select, update

    async def run():
        async with async_session_factory() as session:
            result = await session.execute(select(Video).where(Video.id == video_id))
            video = result.scalar_one_or_none()
            if not video or not video.original_file_key:
                logger.error(f"Video {video_id} not found or no original file")
                return

            await session.execute(
                update(Video).where(Video.id == video_id).values(status=VideoStatus.PROCESSING)
            )
            await session.commit()

            with tempfile.TemporaryDirectory() as tmpdir:
                # Download original
                input_path = os.path.join(tmpdir, "original")
                try:
                    data = download_file(settings.MINIO_BUCKET_VIDEOS, video.original_file_key)
                    with open(input_path, "wb") as f:
                        f.write(data)
                except Exception as e:
                    logger.error(f"Failed to download original for video {video_id}: {e}")
                    await session.execute(
                        update(Video).where(Video.id == video_id).values(status=VideoStatus.FAILED)
                    )
                    await session.commit()
                    return

                # Probe
                probe_data = probe_video(input_path)
                if not probe_data:
                    await session.execute(
                        update(Video).where(Video.id == video_id).values(status=VideoStatus.FAILED)
                    )
                    await session.commit()
                    return

                duration = get_video_duration(probe_data)
                resolution = get_video_resolution(probe_data)
                source_height = resolution[1] if resolution else 720

                if duration:
                    await session.execute(
                        update(Video).where(Video.id == video_id).values(duration=duration)
                    )
                    await session.commit()

                target_resolutions = get_target_resolutions(source_height)
                all_success = True

                for res_name in target_resolutions:
                    output_path = os.path.join(tmpdir, f"{res_name}.mp4")

                    # Create video_file record
                    vf = VideoFile(
                        video_id=video_id,
                        resolution=VideoResolution(res_name),
                        status=VideoFileStatus.PROCESSING,
                    )
                    session.add(vf)
                    await session.flush()
                    await session.commit()

                    success = transcode_video(input_path, output_path, res_name)

                    if success and os.path.exists(output_path):
                        file_size = os.path.getsize(output_path)
                        file_key = f"transcoded/{video_id}/{res_name}.mp4"
                        with open(output_path, "rb") as f:
                            upload_file(settings.MINIO_BUCKET_VIDEOS, file_key, f.read(), "video/mp4")

                        file_url = get_presigned_url(settings.MINIO_BUCKET_VIDEOS, file_key)
                        vf.file_key = file_key
                        vf.file_url = file_url
                        vf.file_size = file_size
                        vf.duration = duration
                        vf.container = "mp4"
                        vf.codec = "h264"
                        vf.status = VideoFileStatus.COMPLETED

                        from app.services.transcoding_service import RESOLUTION_MAP
                        res_info = RESOLUTION_MAP.get(res_name, {})
                        vf.width = res_info.get("width")
                        vf.height = res_info.get("height")
                        vf.bitrate = res_info.get("bitrate")
                    else:
                        vf.status = VideoFileStatus.FAILED
                        all_success = False
                        logger.error(f"Transcoding failed for video {video_id} at {res_name}")

                    await session.commit()

                final_status = VideoStatus.READY if all_success else VideoStatus.FAILED
                await session.execute(
                    update(Video).where(Video.id == video_id).values(status=final_status)
                )
                await session.commit()
                logger.info(f"Video {video_id} processing completed with status {final_status.value}")

    try:
        asyncio.get_event_loop().run_until_complete(run())
    except Exception as exc:
        logger.error(f"Video processing failed for {video_id}: {exc}")
        raise self.retry(exc=exc)
