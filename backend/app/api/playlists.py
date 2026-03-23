"""Playlist API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.schemas.playlist import PlaylistCreate, PlaylistUpdate, PlaylistResponse, PlaylistItemCreate, PlaylistItemReorder
from app.schemas.common import MessageResponse, PaginatedResponse
from app.services.playlist_service import PlaylistService
from app.utils.pagination import PaginatedResponse as PR
from app.utils.permissions import get_user_channel

router = APIRouter(prefix="/api/playlists", tags=["playlists"])


@router.post("", response_model=PlaylistResponse, status_code=status.HTTP_201_CREATED)
async def create_playlist(data: PlaylistCreate, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    channel = await get_user_channel(db, current_user["user_id"])
    service = PlaylistService(db)
    playlist = await service.create(channel.id, data.title, data.description, data.visibility)
    return playlist


@router.get("/channel/{channel_id}", response_model=PaginatedResponse)
async def list_channel_playlists(channel_id: int, page: int = 1, page_size: int = 20, db: AsyncSession = Depends(get_db)):
    service = PlaylistService(db)
    playlists, total = await service.list_channel_playlists(channel_id, page, page_size)
    return PR.create([PlaylistResponse.model_validate(p) for p in playlists], total, page, page_size)


@router.get("/my", response_model=PaginatedResponse)
async def list_my_playlists(page: int = 1, page_size: int = 20, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    channel = await get_user_channel(db, current_user["user_id"])
    service = PlaylistService(db)
    playlists, total = await service.list_channel_playlists(channel.id, page, page_size, include_private=True)
    return PR.create([PlaylistResponse.model_validate(p) for p in playlists], total, page, page_size)


@router.get("/{playlist_id}", response_model=PlaylistResponse)
async def get_playlist(playlist_id: int, db: AsyncSession = Depends(get_db)):
    service = PlaylistService(db)
    playlist = await service.get_by_id(playlist_id)
    if not playlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found")
    return playlist


@router.put("/{playlist_id}", response_model=PlaylistResponse)
async def update_playlist(playlist_id: int, data: PlaylistUpdate, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    channel = await get_user_channel(db, current_user["user_id"])
    service = PlaylistService(db)
    playlist = await service.get_by_id(playlist_id)
    if not playlist or playlist.channel_id != channel.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your playlist")
    updated = await service.update(playlist_id, **data.model_dump(exclude_unset=True))
    return updated


@router.delete("/{playlist_id}", response_model=MessageResponse)
async def delete_playlist(playlist_id: int, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    channel = await get_user_channel(db, current_user["user_id"])
    service = PlaylistService(db)
    playlist = await service.get_by_id(playlist_id)
    if not playlist or playlist.channel_id != channel.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your playlist")
    await service.delete(playlist_id)
    return MessageResponse(message="Playlist deleted")


@router.post("/{playlist_id}/items", status_code=status.HTTP_201_CREATED)
async def add_playlist_item(playlist_id: int, data: PlaylistItemCreate, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    channel = await get_user_channel(db, current_user["user_id"])
    service = PlaylistService(db)
    playlist = await service.get_by_id(playlist_id)
    if not playlist or playlist.channel_id != channel.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your playlist")
    try:
        item = await service.add_item(playlist_id, data.video_id, data.position)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return {"id": item.id, "video_id": item.video_id, "position": item.position}


@router.delete("/{playlist_id}/items/{video_id}", response_model=MessageResponse)
async def remove_playlist_item(playlist_id: int, video_id: int, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    channel = await get_user_channel(db, current_user["user_id"])
    service = PlaylistService(db)
    playlist = await service.get_by_id(playlist_id)
    if not playlist or playlist.channel_id != channel.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your playlist")
    success = await service.remove_item(playlist_id, video_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found in playlist")
    return MessageResponse(message="Item removed from playlist")


@router.put("/{playlist_id}/items/reorder")
async def reorder_playlist_item(playlist_id: int, data: PlaylistItemReorder, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    channel = await get_user_channel(db, current_user["user_id"])
    service = PlaylistService(db)
    playlist = await service.get_by_id(playlist_id)
    if not playlist or playlist.channel_id != channel.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your playlist")
    item = await service.reorder_item(data.item_id, data.new_position)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return {"id": item.id, "position": item.position}


@router.get("/{playlist_id}/items", response_model=PaginatedResponse)
async def get_playlist_items(playlist_id: int, page: int = 1, page_size: int = 50, db: AsyncSession = Depends(get_db)):
    service = PlaylistService(db)
    items, total = await service.get_items(playlist_id, page, page_size)
    return PR.create(
        [{"id": i.id, "video_id": i.video_id, "position": i.position, "added_at": i.added_at.isoformat() if i.added_at else None} for i in items],
        total, page, page_size,
    )
