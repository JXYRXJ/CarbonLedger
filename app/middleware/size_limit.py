import logging
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings

logger = logging.getLogger("app.middleware.size_limit")


class ContentLengthLimitMiddleware(BaseHTTPMiddleware):
    """
    Security Middleware that rejects payloads exceeding the maximum configured content length limit (e.g. 10MB).
    Prevents large file/JSON payload Denial of Service (DoS) exploits.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        content_length_str = request.headers.get("Content-Length")
        if content_length_str:
            try:
                content_length = int(content_length_str)
                max_length = settings.MAX_CONTENT_LENGTH
                if content_length > max_length:
                    logger.warning(
                        f"Request rejected: Content-Length ({content_length} bytes) exceeds limit ({max_length} bytes) for path '{request.url.path}'"
                    )
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={
                            "success": False,
                            "message": "Payload Too Large: Content length exceeds maximum allowed size"
                        }
                    )
            except ValueError:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "success": False,
                        "message": "Bad Request: Invalid Content-Length header"
                    }
                )
                
        return await call_next(request)
