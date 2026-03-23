"""Video API routes."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import get_current_user, require_any_authenticated
from app.schemas.video import VideoCreate, VideoUpdate, VideoResponse, VideoBriefResponse
from app.schemas.comment import CommentCreate, CommentUpdate, CommentResponse
from app.schemas.common import MessageResponse, PaginatedResponse
from app.services.video_service import VideoService
from app.services.channel_service import ChannelService
from app.tasks.transcoding_tasks import process_video
from app.tasks.thumbnail_tasks import generate_video_thumbnail
from app.tasks.notification_tasks import notify_subscribers_new_video, notify_comment_reply
from app.utils.file_utils import validate_video_upload, validate_image_upload, generate_file_key
from app.utils.minio_client import upload_file, get_presigned_url
from app.utils.pagination import PaginatedResponse as PR
from app.utils.permissions import get_user_channel
from app.config import settings

router = APIRouter(prefix="/api/videos", tags=["videos"])


@router.post("", response_model=VideoResponse, status_code=status.HTTP_201_CREATED)
async def create_video(data: VideoCreate, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    channel = await get_user_channel(db, current_user["user_id"])
    service = VideoService(db)
    video = await service.create(
        channel_id=channel.id,
        title=data.title,
        description=data.description,
        category_id=data.category_id,
        visibility=data.visibility,
        tags=data.tags,
        is_age_restricted=data.is_age_restricted,
        is_comments_disabled=data.is_comments_disabled,
        language=data.language,
    )
    return video


@router.post("/{video_id}/upload", response_model=VideoResponse)
async def upload_video_file(video_id: int, file: UploadFile = File(...), current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    channel = await get_user_channel(db, current_user["user_id"])
    service = VideoService(db)
    video = await service.get_by_id(video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    if video.channel_id != channel.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your video")

    validate_video_upload(file)
    data = await file.read()
    file_key = generate_file_key(f"originals/{video_id}", file.filename)
    upload_file(settings.MINIO_BUCKET_VIDEOS, file_key, data, file.content_type)
    await service.set_file_info(video_id, file_key, file.filename, len(data))

    # Trigger async transcoding and thumbnail generation
    process_video.delay(video_id)
    generate_video_thumbnail.delay(video_id)

    video = await service.get_by_id(video_id)
    return video


@router.post("/{video_id}/thumbnail", response_model=VideoResponse)
async def upload_custom_thumbnail(video_id: int, file: UploadFile = File(...), current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    channel = await get_user_channel(db, current_user["user_id"])
    service = VideoService(db)
    video = await service.get_by_id(video_id)
    if not video or video.channel_id != channel.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your video")

    validate_image_upload(file, settings.MAX_THUMBNAIL_SIZE_MB)
    data = await file.read()
    key = generate_file_key(f"thumbnails/{video_id}", file.filename)
    upload_file(settings.MINIO_BUCKET_THUMBNAILS, key, data, file.content_type)
    url = get_presigned_url(settings.MINIO_BUCKET_THUMBNAILS, key)
    await service.update(video_id, thumbnail_key=key, thumbnail_url=url)
    video = await service.get_by_id(video_id)
    return video


@router.get("", response_model=PaginatedResponse)
async def list_public_videos(page: int = 1, page_size: int = 20, category_id: int = None, db: AsyncSession = Depends(get_db)):
    service = VideoService(db)
    videos, total = await service.list_public_videos(page, page_size, category_id)
    return PR.create([VideoBriefResponse.model_validate(v) for v in videos], total, page, page_size)


@router.get("/channel/{channel_id}", response_model=PaginatedResponse)
async def list_channel_videos(channel_id: int, page: int = 1, page_size: int = 20, db: AsyncSession = Depends(get_db)):
    service = VideoService(db)
    videos, total = await service.list_channel_videos(channel_id, page, page_size)
    return PR.create([VideoBriefResponse.model_validate(v) for v in videos], total, page, page_size)


@router.get("/my", response_model=PaginatedResponse)
async def list_my_videos(page: int = 1, page_size: int = 20, status_filter: str = None, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    channel = await get_user_channel(db, current_user["user_id"])
    service = VideoService(db)
    videos, total = await service.list_channel_videos(channel.id, page, page_size, status_filter)
    return PR.create([VideoBriefResponse.model_validate(v) for v in videos], total, page, page_size)


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(video_id: int, db: AsyncSession = Depends(get_db)):
    service = VideoService(db)
    video = await service.get_by_id(video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    return video


@router.get("/slug/{slug}", response_model=VideoResponse)
async def get_video_by_slug(slug: str, db: AsyncSession = Depends(get_db)):
    service = VideoService(db)
    video = await service.get_by_slug(slug)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    return video


@router.put("/{video_id}", response_model=VideoResponse)
async def update_video(video_id: int, data: VideoUpdate, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    channel = await get_user_channel(db, current_user["user_id"])
    service = VideoService(db)
    video = await service.get_by_id(video_id)
    if not video or video.channel_id != channel.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your video")
    update_data = data.model_dump(exclude_unset=True)
    tags = update_data.pop("tags", None)
    updated = await service.update(video_id, tags=tags, **update_data)
    return updated


@router.delete("/{video_id}", response_model=MessageResponse)
async def delete_video(video_id: int, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    channel = await get_user_channel(db, current_user["user_id"])
    service = VideoService(db)
    video = await service.get_by_id(video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    if video.channel_id != channel.id and current_user.get("role") not in ("admin", "superadmin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your video")
    await service.delete(video_id)
    return MessageResponse(message="Video deleted")


@router.post("/{video_id}/publish", response_model=VideoResponse)
async def publish_video(video_id: int, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    channel = await get_user_channel(db, current_user["user_id"])
    service = VideoService(db)
    video = await service.get_by_id(video_id)
    if not video or video.channel_id != channel.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your video")
    published = await service.publish(video_id)
    if not published:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Video is not ready for publishing")
    notify_subscribers_new_video.delay(channel.id, video_id, video.title)
    return published


@router.post("/{video_id}/view")
async def record_view(video_id: int, db: AsyncSession = Depends(get_db)):
    service = VideoService(db)
    video = await service.get_by_id(video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    await service.increment_views(video_id)
    return {"view_count": video.view_count + 1}


# Like/Dislike
@router.post("/{video_id}/like")
async def like_video(video_id: int, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = VideoService(db)
    video = await service.get_by_id(video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    await service.like_video(current_user["user_id"], video_id, "like")
    return {"message": "Like toggled"}


@router.post("/{video_id}/dislike")
async def dislike_video(video_id: int, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = VideoService(db)
    video = await service.get_by_id(video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    await service.like_video(current_user["user_id"], video_id, "dislike")
    return {"message": "Dislike toggled"}


@router.get("/{video_id}/like-status")
async def get_like_status(video_id: int, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = VideoService(db)
    like = await service.get_user_like(current_user["user_id"], video_id)
    return {"like_type": like.like_type.value if like else None}


# Comments
@router.get("/{video_id}/comments", response_model=PaginatedResponse)
async def get_comments(video_id: int, parent_id: int = None, page: int = 1, page_size: int = 20, db: AsyncSession = Depends(get_db)):
    service = VideoService(db)
    comments, total = await service.get_comments(video_id, parent_id, page, page_size)
    return PR.create([CommentResponse.model_validate(c) for c in comments], total, page, page_size)


@router.post("/{video_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(video_id: int, data: CommentCreate, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = VideoService(db)
    video = await service.get_by_id(video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    if video.is_comments_disabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Comments are disabled for this video")
    comment = await service.add_comment(video_id, current_user["user_id"], data.body, data.parent_id)
    if data.parent_id:
        notify_comment_reply.delay(comment.id, current_user["user_id"], video_id)
    return comment


@router.put("/comments/{comment_id}", response_model=CommentResponse)
async def update_comment(comment_id: int, data: CommentUpdate, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = VideoService(db)
    comment = await service.update_comment(comment_id, current_user["user_id"], data.body)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found or not yours")
    return comment


@router.delete("/comments/{comment_id}", response_model=MessageResponse)
async def delete_comment(comment_id: int, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = VideoService(db)
    is_admin = current_user.get("role") in ("admin", "superadmin")
    success = await service.delete_comment(comment_id, current_user["user_id"], is_admin)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found or not yours")
    return MessageResponse(message="Comment deleted")


@router.get("/{video_id}/tags")
async def get_video_tags(video_id: int, db: AsyncSession = Depends(get_db)):
    service = VideoService(db)
    tags = await service.get_video_tags(video_id)
    return [{"id": t.id, "name": t.name, "slug": t.slug} for t in tags]
