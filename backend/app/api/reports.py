"""Report API routes (user-facing)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.report import Report, ReportReason, ReportStatus, ReportTargetType
from app.schemas.report import ReportCreate
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_report(data: ReportCreate, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Check for duplicate report
    existing = await db.execute(
        select(Report).where(
            Report.reporter_id == current_user["user_id"],
            Report.target_type == ReportTargetType(data.target_type),
            Report.target_id == data.target_id,
            Report.status == ReportStatus.PENDING,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You have already reported this content")

    report = Report(
        reporter_id=current_user["user_id"],
        target_type=ReportTargetType(data.target_type),
        target_id=data.target_id,
        reason=ReportReason(data.reason),
        description=data.description,
    )
    db.add(report)
    await db.flush()
    return MessageResponse(message="Report submitted. Our team will review it shortly.")
