"""Application configuration using pydantic-settings."""

from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    APP_NAME: str = "Video Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://videoplatform:videoplatform@localhost:5432/videoplatform"
    DATABASE_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "super-secret-jwt-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # MinIO / S3
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_BUCKET_VIDEOS: str = "videos"
    MINIO_BUCKET_THUMBNAILS: str = "thumbnails"
    MINIO_BUCKET_AVATARS: str = "avatars"
    MINIO_BUCKET_BANNERS: str = "banners"

    # SMTP / Email
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = False
    SMTP_FROM_EMAIL: str = "noreply@video_platform.io"
    SMTP_FROM_NAME: str = "Video Platform"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Frontend URLs
    FRONTEND_URL: str = "http://localhost:3000"
    FRONTEND_STUDIO_URL: str = "http://localhost:3001"
    FRONTEND_ADMIN_URL: str = "http://localhost:3002"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
    ]

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # File Upload
    MAX_VIDEO_SIZE_MB: int = 5120
    MAX_THUMBNAIL_SIZE_MB: int = 10
    MAX_AVATAR_SIZE_MB: int = 5
    MAX_BANNER_SIZE_MB: int = 10
    ALLOWED_VIDEO_TYPES: List[str] = [
        "video/mp4", "video/webm", "video/quicktime", "video/x-msvideo",
        "video/x-matroska", "video/mpeg",
    ]
    ALLOWED_IMAGE_TYPES: List[str] = [
        "image/jpeg", "image/png", "image/webp", "image/gif",
    ]

    # Transcoding
    TRANSCODING_RESOLUTIONS: List[str] = ["360p", "480p", "720p", "1080p"]
    FFMPEG_PATH: str = "ffmpeg"
    FFPROBE_PATH: str = "ffprobe"

    # Platform Settings
    MAX_VIDEOS_PER_CHANNEL: int = 10000
    MAX_PLAYLISTS_PER_CHANNEL: int = 500
    MAX_COMMENT_DEPTH: int = 5
    TRENDING_WINDOW_HOURS: int = 48
    DEFAULT_PAGE_SIZE: int = 20

    model_config = {"env_prefix": "", "env_file": ".env", "extra": "ignore"}


settings = Settings()
