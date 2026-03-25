import logging
import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

REQUESTS_RATE_LIMIT = 100  # requests
REQUESTS_RATE_PERIOD = 60  # seconds
_rate_limit_store = defaultdict(list)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """In-memory rate limiting for single-instance deployments.

    Use a shared backend such as Redis for distributed deployments.
    """

    async def dispatch(self, request: Request, call_next):
        ip = request.client.host
        now = time.time()
        window = [
            t for t in _rate_limit_store[ip] if now - t < REQUESTS_RATE_PERIOD
        ]
        window.append(now)
        _rate_limit_store[ip] = window
        if len(window) > REQUESTS_RATE_LIMIT:
            logger = logging.getLogger(__name__)
            logger.warning(f"Rate limit exceeded for IP: {ip}")
            return Response("Too Many Requests", status_code=429)
        response = await call_next(request)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=63072000; includeSubDomains"
        )
        return response


__all__ = ["RateLimitMiddleware", "SecurityHeadersMiddleware"]
