"""Playlist service."""

from typing import Optional

from sqlalchemy import select, func, update, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.playlist import Playlist, PlaylistVisibility
from app.models.playlist_item import PlaylistItem
from app.utils.slug_utils import generate_slug


class PlaylistService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, playlist_id: int) -> Optional[Playlist]:
        result = await self.db.execute(select(Playlist).where(Playlist.id == playlist_id))
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Playlist]:
        result = await self.db.execute(select(Playlist).where(Playlist.slug == slug))
        return result.scalar_one_or_none()

    async def create(self, channel_id: int, title: str, description: Optional[str] = None, visibility: str = "public") -> Playlist:
        slug = generate_slug(title)
        playlist = Playlist(
            channel_id=channel_id,
            title=title,
            description=description,
            slug=slug,
            visibility=PlaylistVisibility(visibility),
        )
        self.db.add(playlist)
        await self.db.flush()
        return playlist

    async def update(self, playlist_id: int, **kwargs) -> Optional[Playlist]:
        playlist = await self.get_by_id(playlist_id)
        if not playlist:
            return None
        for key, value in kwargs.items():
            if hasattr(playlist, key) and value is not None:
                if key == "visibility":
                    value = PlaylistVisibility(value)
                setattr(playlist, key, value)
        await self.db.flush()
        return playlist

    async def delete(self, playlist_id: int) -> bool:
        playlist = await self.get_by_id(playlist_id)
        if not playlist:
            return False
        await self.db.delete(playlist)
        await self.db.flush()
        return True

    async def add_item(self, playlist_id: int, video_id: int, position: Optional[int] = None) -> PlaylistItem:
        # Check duplicate
        existing = await self.db.execute(
            select(PlaylistItem).where(
                PlaylistItem.playlist_id == playlist_id,
                PlaylistItem.video_id == video_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("Video already in playlist")

        if position is None:
            max_pos_result = await self.db.execute(
                select(func.max(PlaylistItem.position)).where(PlaylistItem.playlist_id == playlist_id)
            )
            max_pos = max_pos_result.scalar() or 0
            position = max_pos + 1

        item = PlaylistItem(playlist_id=playlist_id, video_id=video_id, position=position)
        self.db.add(item)
        await self.db.execute(
            update(Playlist).where(Playlist.id == playlist_id).values(video_count=Playlist.video_count + 1)
        )
        await self.db.flush()
        return item

    async def remove_item(self, playlist_id: int, video_id: int) -> bool:
        result = await self.db.execute(
            select(PlaylistItem).where(
                PlaylistItem.playlist_id == playlist_id,
                PlaylistItem.video_id == video_id,
            )
        )
        item = result.scalar_one_or_none()
        if not item:
            return False
        await self.db.delete(item)
        await self.db.execute(
            update(Playlist).where(Playlist.id == playlist_id).values(
                video_count=func.greatest(Playlist.video_count - 1, 0)
            )
        )
        await self.db.flush()
        return True

    async def reorder_item(self, item_id: int, new_position: int) -> Optional[PlaylistItem]:
        result = await self.db.execute(select(PlaylistItem).where(PlaylistItem.id == item_id))
        item = result.scalar_one_or_none()
        if not item:
            return None
        item.position = new_position
        await self.db.flush()
        return item

    async def get_items(self, playlist_id: int, page: int = 1, page_size: int = 50):
        query = select(PlaylistItem).where(PlaylistItem.playlist_id == playlist_id)
        count_query = select(func.count()).select_from(PlaylistItem).where(PlaylistItem.playlist_id == playlist_id)
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.offset((page - 1) * page_size).limit(page_size).order_by(PlaylistItem.position.asc())
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def list_channel_playlists(self, channel_id: int, page: int = 1, page_size: int = 20, include_private: bool = False):
        conditions = [Playlist.channel_id == channel_id]
        if not include_private:
            conditions.append(Playlist.visibility == PlaylistVisibility.PUBLIC)

        query = select(Playlist).where(and_(*conditions))
        count_query = select(func.count()).select_from(Playlist).where(and_(*conditions))
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.offset((page - 1) * page_size).limit(page_size).order_by(Playlist.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all(), total
