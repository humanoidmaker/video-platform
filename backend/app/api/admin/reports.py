"""Admin report management routes."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import require_admin
from app.models.report import Report, ReportStatus, ReportTargetType
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.report import ReportResponse, ReportResolve
from app.utils.pagination import PaginatedResponse as PR

router = APIRouter(prefix="/api/admin/reports", tags=["admin-reports"])


@router.get("", response_model=PaginatedResponse)
async def list_reports(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: str = None,
    target_type: str = None,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    conditions = []
    if status_filter:
        conditions.append(Report.status == ReportStatus(status_filter))
    if target_type:
        conditions.append(Report.target_type == ReportTargetType(target_type))

    query = select(Report)
    count_query = select(func.count()).select_from(Report)
    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))
    total = (await db.execute(count_query)).scalar() or 0
    query = query.offset((page - 1) * page_size).limit(page_size).order_by(Report.created_at.desc())
    result = await db.execute(query)
    reports = result.scalars().all()
    return PR.create([ReportResponse.model_validate(r) for r in reports], total, page, page_size)


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(report_id: int, current_user: dict = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return ReportResponse.model_validate(report)


@router.post("/{report_id}/resolve", response_model=MessageResponse)
async def resolve_report(report_id: int, data: ReportResolve, current_user: dict = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    report.status = ReportStatus(data.status)
    report.resolution_note = data.resolution_note
    report.resolved_by = current_user["user_id"]
    report.resolved_at = datetime.now(timezone.utc)
    await db.flush()
    return MessageResponse(message=f"Report {data.status}")
