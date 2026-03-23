"""User schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    username: str
    display_name: str
    bio: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    display_name: str
    bio: Optional[str] = None
    role: str
    avatar_url: Optional[str] = None
    is_active: bool
    email_verified: bool
    last_login_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None


class UserBriefResponse(BaseModel):
    id: int
    username: str
    display_name: str
    avatar_url: Optional[str] = None

    model_config = {"from_attributes": True}
