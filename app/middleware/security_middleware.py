import json
import logging
from typing import Any, Callable, Dict, List, Set, Union
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings

logger = logging.getLogger("app.middleware.security")

SENSITIVE_KEYS: Set[str] = {
    "password", "secret", "private_key", "token", "access_token",
    "refresh_token", "client_secret", "authorization"
}


def redact_sensitive_data(data: Any) -> Any:
    """
    Recursively redacts values for sensitive keys in dictionaries and lists.
    """
    if isinstance(data, dict):
        redacted = {}
        for k, v in data.items():
            if str(k).lower() in SENSITIVE_KEYS:
                redacted[k] = "[REDACTED]"
            else:
                redacted[k] = redact_sensitive_data(v)
        return redacted
    elif isinstance(data, list):
        return [redact_sensitive_data(item) for item in data]
    return data


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces security response headers and filters sensitive output data.
    """
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Enforce OWASP security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none';"
        response.headers["Referrer-Policy"] = "no-referrer"

        # Inject HSTS in production environments
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"

        # Intercept and redact sensitive data from JSON responses
        content_type = response.headers.get("content-type", "")
        content_encoding = response.headers.get("content-encoding", "")
        if "application/json" in content_type and "gzip" not in content_encoding:
            # We only filter if route is not swagger/openapi documentation to avoid breaking UI spec
            path = request.url.path
            if not (
                path.endswith("/openapi.json")
                or path.endswith("/docs")
                or path.endswith("/redoc")
                or "/auth" in path
            ):
                try:
                    # Read the response body
                    body_parts = [section async for section in response.body_iterator]
                    # Restore response iterator so starlette can stream it later
                    response.body_iterator = _create_iterator(body_parts)
                    
                    full_body = b"".join(body_parts)
                    if full_body:
                        json_data = json.loads(full_body.decode("utf-8"))
                        redacted_json = redact_sensitive_data(json_data)
                        
                        # Rebuild response with redacted content
                        new_body = json.dumps(redacted_json).encode("utf-8")
                        response.headers["content-length"] = str(len(new_body))
                        response.body_iterator = _create_iterator([new_body])
                except Exception as exc:
                    logger.error(f"Error filtering sensitive data in security middleware: {str(exc)}")

        return response


async def _create_iterator(parts: List[bytes]):
    """
    Asynchronous generator to rebuild response body streams.
    """
    for part in parts:
        yield part
