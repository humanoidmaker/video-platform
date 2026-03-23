"""Notifications API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.notification import NotificationResponse
from app.services.notification_service import NotificationService
from app.utils.pagination import PaginatedResponse as PR

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=PaginatedResponse)
async def list_notifications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    unread_only: bool = False,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    notifications, total = await service.get_user_notifications(
        current_user["user_id"], page, page_size, unread_only
    )
    return PR.create([NotificationResponse.model_validate(n) for n in notifications], total, page, page_size)


@router.get("/unread-count")
async def unread_count(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = NotificationService(db)
    count = await service.get_unread_count(current_user["user_id"])
    return {"unread_count": count}


@router.post("/{notification_id}/read", response_model=MessageResponse)
async def mark_as_read(notification_id: int, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = NotificationService(db)
    success = await service.mark_as_read(notification_id, current_user["user_id"])
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return MessageResponse(message="Marked as read")


@router.post("/read-all", response_model=MessageResponse)
async def mark_all_as_read(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = NotificationService(db)
    count = await service.mark_all_as_read(current_user["user_id"])
    return MessageResponse(message=f"Marked {count} notifications as read")


@router.delete("/{notification_id}", response_model=MessageResponse)
async def delete_notification(notification_id: int, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = NotificationService(db)
    success = await service.delete(notification_id, current_user["user_id"])
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return MessageResponse(message="Notification deleted")
