"""Search schemas."""

from typing import List, Optional
from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    q: str = Field(min_length=1, max_length=200)
    type: Optional[str] = Field(None, pattern="^(video|channel|playlist)$")
    category_id: Optional[int] = None
    sort_by: Optional[str] = Field(None, pattern="^(relevance|date|views|rating)$")
    duration_filter: Optional[str] = Field(None, pattern="^(short|medium|long)$")
    upload_date: Optional[str] = Field(None, pattern="^(today|week|month|year)$")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
