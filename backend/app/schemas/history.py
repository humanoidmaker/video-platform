"""Watch history schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class WatchHistoryUpdate(BaseModel):
    watch_duration: float = 0.0
    progress_percent: float = 0.0
    last_position: float = 0.0


class WatchHistoryResponse(BaseModel):
    id: int
    video_id: int
    watch_duration: float = 0.0
    progress_percent: float = 0.0
    last_position: float = 0.0
    watched_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
