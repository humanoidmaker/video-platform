"""Admin system routes."""

import platform

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.middleware.auth_middleware import require_admin

router = APIRouter(prefix="/api/admin/system", tags=["admin-system"])


@router.get("/health")
async def system_health(current_user: dict = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    # Database check
    db_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    # Redis check
    redis_ok = False
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        redis_ok = True
    except Exception:
        pass

    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "redis": "connected" if redis_ok else "disconnected",
        "python_version": platform.python_version(),
        "app_version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@router.get("/config")
async def system_config(current_user: dict = Depends(require_admin)):
    return {
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "max_video_size_mb": settings.MAX_VIDEO_SIZE_MB,
        "transcoding_resolutions": settings.TRANSCODING_RESOLUTIONS,
        "trending_window_hours": settings.TRENDING_WINDOW_HOURS,
        "rate_limit_per_minute": settings.RATE_LIMIT_PER_MINUTE,
    }


@router.post("/clear-cache")
async def clear_cache(current_user: dict = Depends(require_admin)):
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL)
        r.flushdb()
        return {"message": "Cache cleared"}
    except Exception as e:
        return {"message": f"Cache clear failed: {str(e)}"}
