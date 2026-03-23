"""Admin user management routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import require_admin
from app.models.user import User, UserRole
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.user import UserResponse
from app.utils.pagination import PaginatedResponse as PR

router = APIRouter(prefix="/api/admin/users", tags=["admin-users"])


@router.get("", response_model=PaginatedResponse)
async def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    role: str = None,
    search: str = None,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(User)
    count_query = select(func.count()).select_from(User)
    if role:
        query = query.where(User.role == UserRole(role))
        count_query = count_query.where(User.role == UserRole(role))
    if search:
        search_filter = User.email.ilike(f"%{search}%") | User.username.ilike(f"%{search}%") | User.display_name.ilike(f"%{search}%")
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)
    total = (await db.execute(count_query)).scalar() or 0
    query = query.offset((page - 1) * page_size).limit(page_size).order_by(User.created_at.desc())
    result = await db.execute(query)
    users = result.scalars().all()
    return PR.create([UserResponse.model_validate(u) for u in users], total, page, page_size)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, current_user: dict = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse.model_validate(user)


@router.post("/{user_id}/ban", response_model=MessageResponse)
async def ban_user(user_id: int, current_user: dict = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.role in (UserRole.ADMIN, UserRole.SUPERADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot ban admin users")
    user.is_banned = True
    user.is_active = False
    await db.flush()
    return MessageResponse(message="User banned")


@router.post("/{user_id}/unban", response_model=MessageResponse)
async def unban_user(user_id: int, current_user: dict = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.is_banned = False
    user.is_active = True
    await db.flush()
    return MessageResponse(message="User unbanned")


@router.put("/{user_id}/role", response_model=MessageResponse)
async def change_user_role(user_id: int, role: str = Query(pattern="^(viewer|creator|admin)$"), current_user: dict = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    if current_user.get("role") != "superadmin" and role == "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only superadmins can promote to admin")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.role = UserRole(role)
    await db.flush()
    return MessageResponse(message=f"User role changed to {role}")
