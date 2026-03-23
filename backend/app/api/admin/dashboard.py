"""Admin dashboard routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import require_admin
from app.schemas.analytics import DashboardStats
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/admin/dashboard", tags=["admin-dashboard"])


@router.get("", response_model=DashboardStats)
async def get_dashboard(current_user: dict = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    service = AnalyticsService(db)
    stats = await service.get_dashboard_stats()
    return DashboardStats(**stats)
