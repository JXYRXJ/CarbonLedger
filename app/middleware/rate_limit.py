import time
import logging
from collections import defaultdict
from typing import Dict, List
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("app.middleware.rate_limit")


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    In-memory Sliding Window rate limiter middleware.
    Restricts request volume from any single IP to 100 requests per 60 seconds.
    """
    def __init__(self, app, requests_limit: int = 100, window_sec: int = 60) -> None:
        super().__init__(app)
        self.requests_limit = requests_limit
        self.window_sec = window_sec
        # client_ip -> list of timestamps
        self.history: Dict[str, List[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next) -> Response:
        # Get client IP
        client_ip = request.client.host if request.client else "127.0.0.1"
        
        # Exclude testing environment from rate limiting to prevent test blockages
        # Unless the test explicitly requests to check rate limits via x-test-rate-limit header
        from app.core.config import settings
        if settings.ENVIRONMENT == "testing" and "x-test-rate-limit" not in request.headers:
            return await call_next(request)

        # Exclude API documentation paths from rate limiting to prevent UI lockup
        path = request.url.path
        if path.startswith(("/docs", "/redoc", "/api/v1/openapi.json", "/api/v1/health")):
            return await call_next(request)

        current_time = time.time()
        
        # Clean history for this IP
        timestamps = self.history[client_ip]
        while timestamps and timestamps[0] < current_time - self.window_sec:
            timestamps.pop(0)

        # Check limit
        if len(timestamps) >= self.requests_limit:
            logger.warning(f"Rate limit exceeded for IP '{client_ip}' on path '{path}'")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "message": "Too Many Requests: Rate limit exceeded. Please try again later."
                }
            )

        # Log timestamp and pass
        timestamps.append(current_time)
        return await call_next(request)
