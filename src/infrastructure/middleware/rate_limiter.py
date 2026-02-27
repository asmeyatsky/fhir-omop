"""
Rate Limiter Middleware

Architectural Intent:
- Token bucket rate limiting per tenant and per IP
- In-memory implementation (swappable to Redis in production)
- Configurable limits per tenant
- Returns 429 Too Many Requests when exceeded
"""
from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


@dataclass
class TokenBucket:
    """Token bucket for rate limiting."""
    capacity: int
    refill_rate: float  # tokens per second
    tokens: float = 0.0
    last_refill: float = field(default_factory=time.monotonic)

    def __post_init__(self):
        self.tokens = float(self.capacity)

    def consume(self) -> bool:
        """Try to consume a token. Returns True if allowed."""
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False

    @property
    def retry_after(self) -> int:
        """Seconds until a token is available."""
        if self.tokens >= 1:
            return 0
        return max(1, int((1 - self.tokens) / self.refill_rate))


EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Per-tenant and per-IP rate limiting middleware."""

    def __init__(
        self,
        app,
        requests_per_minute: int = 100,
        burst_size: int = 20,
    ):
        super().__init__(app)
        self._requests_per_minute = requests_per_minute
        self._burst_size = burst_size
        self._buckets: dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(
                capacity=burst_size,
                refill_rate=requests_per_minute / 60.0,
            )
        )

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        # Rate limit key: tenant_id or IP
        tenant_id = request.headers.get("x-tenant-id")
        client_ip = request.client.host if request.client else "unknown"
        limit_key = f"tenant:{tenant_id}" if tenant_id else f"ip:{client_ip}"

        bucket = self._buckets[limit_key]
        if not bucket.consume():
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please slow down.",
                    "retry_after": bucket.retry_after,
                },
                headers={"Retry-After": str(bucket.retry_after)},
            )

        response = await call_next(request)
        return response
