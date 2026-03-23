"""Channel API routes."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import get_current_user, require_any_authenticated
from app.schemas.channel import ChannelCreate, ChannelUpdate, ChannelResponse, ChannelBriefResponse
from app.schemas.common import MessageResponse, PaginatedResponse
from app.services.channel_service import ChannelService
from app.tasks.notification_tasks import notify_new_subscriber
from app.utils.file_utils import validate_image_upload, generate_file_key
from app.utils.minio_client import upload_file, get_presigned_url
from app.config import settings

router = APIRouter(prefix="/api/channels", tags=["channels"])


@router.post("", response_model=ChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_channel(data: ChannelCreate, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = ChannelService(db)
    existing = await service.get_by_owner(current_user["user_id"])
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You already have a channel")
    try:
        channel = await service.create(current_user["user_id"], data.handle, data.name, data.description)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return channel


@router.get("", response_model=PaginatedResponse)
async def list_channels(page: int = 1, page_size: int = 20, search: str = None, db: AsyncSession = Depends(get_db)):
    service = ChannelService(db)
    channels, total = await service.list_channels(page, page_size, search)
    from app.utils.pagination import PaginatedResponse as PR
    return PR.create([ChannelBriefResponse.model_validate(c) for c in channels], total, page, page_size)


@router.get("/me", response_model=ChannelResponse)
async def get_my_channel(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = ChannelService(db)
    channel = await service.get_by_owner(current_user["user_id"])
    if not channel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You don't have a channel yet")
    return channel


@router.get("/{channel_id}", response_model=ChannelResponse)
async def get_channel(channel_id: int, db: AsyncSession = Depends(get_db)):
    service = ChannelService(db)
    channel = await service.get_by_id(channel_id)
    if not channel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")
    return channel


@router.get("/handle/{handle}", response_model=ChannelResponse)
async def get_channel_by_handle(handle: str, db: AsyncSession = Depends(get_db)):
    service = ChannelService(db)
    channel = await service.get_by_handle(handle)
    if not channel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")
    return channel


@router.put("/{channel_id}", response_model=ChannelResponse)
async def update_channel(channel_id: int, data: ChannelUpdate, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = ChannelService(db)
    channel = await service.get_by_id(channel_id)
    if not channel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")
    if channel.owner_id != current_user["user_id"] and current_user.get("role") not in ("admin", "superadmin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your channel")
    updated = await service.update(channel_id, **data.model_dump(exclude_unset=True))
    return updated


@router.delete("/{channel_id}", response_model=MessageResponse)
async def delete_channel(channel_id: int, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = ChannelService(db)
    channel = await service.get_by_id(channel_id)
    if not channel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")
    if channel.owner_id != current_user["user_id"] and current_user.get("role") not in ("admin", "superadmin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your channel")
    await service.delete(channel_id)
    return MessageResponse(message="Channel deleted")


@router.post("/{channel_id}/avatar", response_model=ChannelResponse)
async def upload_channel_avatar(channel_id: int, file: UploadFile = File(...), current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = ChannelService(db)
    channel = await service.get_by_id(channel_id)
    if not channel or channel.owner_id != current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your channel")
    validate_image_upload(file, settings.MAX_AVATAR_SIZE_MB)
    data = await file.read()
    key = generate_file_key(f"channels/{channel_id}/avatar", file.filename)
    upload_file(settings.MINIO_BUCKET_AVATARS, key, data, file.content_type)
    url = get_presigned_url(settings.MINIO_BUCKET_AVATARS, key)
    updated = await service.update(channel_id, avatar_key=key, avatar_url=url)
    return updated


@router.post("/{channel_id}/banner", response_model=ChannelResponse)
async def upload_channel_banner(channel_id: int, file: UploadFile = File(...), current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = ChannelService(db)
    channel = await service.get_by_id(channel_id)
    if not channel or channel.owner_id != current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your channel")
    validate_image_upload(file, settings.MAX_BANNER_SIZE_MB)
    data = await file.read()
    key = generate_file_key(f"channels/{channel_id}/banner", file.filename)
    upload_file(settings.MINIO_BUCKET_BANNERS, key, data, file.content_type)
    url = get_presigned_url(settings.MINIO_BUCKET_BANNERS, key)
    updated = await service.update(channel_id, banner_key=key, banner_url=url)
    return updated


@router.post("/{channel_id}/subscribe", response_model=MessageResponse)
async def subscribe(channel_id: int, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = ChannelService(db)
    channel = await service.get_by_id(channel_id)
    if not channel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")
    if channel.owner_id == current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot subscribe to your own channel")
    try:
        await service.subscribe(current_user["user_id"], channel_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    notify_new_subscriber.delay(channel_id, current_user["user_id"])
    return MessageResponse(message="Subscribed successfully")


@router.delete("/{channel_id}/subscribe", response_model=MessageResponse)
async def unsubscribe(channel_id: int, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = ChannelService(db)
    success = await service.unsubscribe(current_user["user_id"], channel_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not subscribed")
    return MessageResponse(message="Unsubscribed successfully")


@router.get("/{channel_id}/subscription-status")
async def subscription_status(channel_id: int, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = ChannelService(db)
    is_sub = await service.is_subscribed(current_user["user_id"], channel_id)
    return {"subscribed": is_sub}
