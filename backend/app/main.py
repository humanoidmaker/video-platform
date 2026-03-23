"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.middleware.request_logger import RequestLoggerMiddleware

# Import routers
from app.api.auth import router as auth_router
from app.api.channels import router as channels_router
from app.api.videos import router as videos_router
from app.api.playlists import router as playlists_router
from app.api.search import router as search_router
from app.api.feed import router as feed_router
from app.api.notifications import router as notifications_router
from app.api.history import router as history_router
from app.api.categories import router as categories_router
from app.api.reports import router as reports_router
from app.api.admin.dashboard import router as admin_dashboard_router
from app.api.admin.users import router as admin_users_router
from app.api.admin.videos import router as admin_videos_router
from app.api.admin.reports import router as admin_reports_router
from app.api.admin.analytics import router as admin_analytics_router
from app.api.admin.system import router as admin_system_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.ENVIRONMENT == "development":
        await init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logger
app.add_middleware(RequestLoggerMiddleware)

# Public routes
app.include_router(auth_router)
app.include_router(channels_router)
app.include_router(videos_router)
app.include_router(playlists_router)
app.include_router(search_router)
app.include_router(feed_router)
app.include_router(notifications_router)
app.include_router(history_router)
app.include_router(categories_router)
app.include_router(reports_router)

# Admin routes
app.include_router(admin_dashboard_router)
app.include_router(admin_users_router)
app.include_router(admin_videos_router)
app.include_router(admin_reports_router)
app.include_router(admin_analytics_router)
app.include_router(admin_system_router)


@app.get("/api/health")
async def health():
    return {"status": "healthy", "app": settings.APP_NAME, "version": settings.APP_VERSION}
