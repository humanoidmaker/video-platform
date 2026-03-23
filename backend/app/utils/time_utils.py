"""Time and date utilities."""

from datetime import datetime, timedelta, timezone


def utcnow() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


def ago(hours: int = 0, days: int = 0) -> datetime:
    """Return a UTC datetime in the past."""
    return utcnow() - timedelta(hours=hours, days=days)


def format_duration(seconds: float) -> str:
    """Format seconds into HH:MM:SS or MM:SS."""
    total = int(seconds)
    h, remainder = divmod(total, 3600)
    m, s = divmod(remainder, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"
