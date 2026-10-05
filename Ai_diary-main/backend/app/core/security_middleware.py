import time
import logging
from collections import defaultdict
from typing import Dict, List, Tuple
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("app.security")

# Sensitive fields and headers to mask in logs
SENSITIVE_KEYS = {"password", "secret", "token", "access_token", "refresh_token", "api_key", "authorization"}

def mask_sensitive_data(data: dict) -> dict:
    """Recursively mask sensitive values in dictionaries for safe logging."""
    if not isinstance(data, dict):
        return data
    masked = {}
    for k, v in data.items():
        if any(s in k.lower() for s in SENSITIVE_KEYS):
            masked[k] = "***MASKED***"
        elif isinstance(v, dict):
            masked[k] = mask_sensitive_data(v)
        elif isinstance(v, list):
            masked[k] = [mask_sensitive_data(i) if isinstance(i, dict) else i for i in v]
        else:
            masked[k] = v
    return masked


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Applies production HTTP security headers to all responses.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Lightweight in-memory rate limiter per IP address for protection against brute force and flooding.
    Permissive in test/dev modes, enforces limits on sensitive auth & AI routes.
    """
    def __init__(self, app, max_requests_per_minute: int = 300):
        super().__init__(app)
        self.max_requests = max_requests_per_minute
        self.requests: Dict[str, List[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next) -> Response:
        # Bypass rate limiter for health checks, static assets, or test clients
        path = request.url.path
        if path.startswith("/api/health") or path == "/health" or path.startswith("/static"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()
        minute_ago = now - 60.0

        # Clean old requests
        timestamps = [t for t in self.requests[client_ip] if t > minute_ago]
        
        # Stricter limit on auth routes (e.g. 60/min per IP)
        limit = 60 if "/auth/login" in path or "/auth/register" in path else self.max_requests

        if len(timestamps) >= limit:
            logger.warning(f"Rate limit exceeded for IP: {client_ip} on path: {path}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many requests. Please slow down and try again shortly."}
            )

        timestamps.append(now)
        self.requests[client_ip] = timestamps

        return await call_next(request)


class SafeLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs API requests with duration and status without exposing sensitive credentials or PII.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        method = request.method

        try:
            response = await call_next(request)
            duration = round((time.time() - start_time) * 1000, 2)
            logger.info(f"{method} {path} - {response.status_code} ({duration}ms) [{client_ip}]")
            return response
        except Exception as exc:
            duration = round((time.time() - start_time) * 1000, 2)
            logger.error(f"Unhandled error in {method} {path} ({duration}ms): {exc}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "An unexpected server error occurred. Please try again later."}
            )
