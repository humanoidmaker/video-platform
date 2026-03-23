"""Rate limiter middleware using Redis."""

import time

from fastapi import HTTPException, Request, status

from app.config import settings


class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.rpm = requests_per_minute
        self._store: dict = {}

    async def check(self, request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        key = f"rate:{client_ip}"
        now = time.time()
        window_start = now - 60

        if key not in self._store:
            self._store[key] = []

        self._store[key] = [t for t in self._store[key] if t > window_start]

        if len(self._store[key]) >= self.rpm:
            retry_after = int(60 - (now - self._store[key][0]))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(max(retry_after, 1))},
            )

        self._store[key].append(now)


rate_limiter = RateLimiter(settings.RATE_LIMIT_PER_MINUTE)
