import logging
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("app.middleware.logging")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that assigns a unique Request ID to each request,
    logs incoming and outgoing requests, and measures the response processing time.
    """
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Extract Request ID from headers if present, otherwise generate a new UUID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Record start time
        start_time = time.perf_counter()

        # Extract user_id and company_id if JWT token is present
        user_id = None
        company_id = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                from jose import jwt
                from app.core.config import settings
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
                user_id = payload.get("sub")
                company_id = payload.get("company_id")
            except Exception:
                pass

        # Log incoming request
        client_host = request.client.host if request.client else "unknown"
        logger.info(
            f"Incoming request: {request.method} {request.url.path} from {client_host}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_host": client_host,
                "user_id": user_id,
                "company_id": company_id
            }
        )

        try:
            # Process the request
            response = await call_next(request)
        except Exception as exc:
            # Log failure and execution duration
            duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            from app.services.metrics import metrics_service
            metrics_service.record_request(duration_sec=(time.perf_counter() - start_time), status_code=500)
            logger.error(
                f"Unhandled exception during {request.method} {request.url.path}: {str(exc)}",
                exc_info=True,
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": 500,
                    "elapsed_ms": duration_ms,
                    "user_id": user_id,
                    "company_id": company_id
                }
            )
            raise exc

        # Measure response processing time
        duration_sec = time.perf_counter() - start_time
        duration_ms = round(duration_sec * 1000.0, 2)

        # Record metrics
        from app.services.metrics import metrics_service
        metrics_service.record_request(duration_sec=duration_sec, status_code=response.status_code)

        # Log response status and request duration
        logger.info(
            f"Request completed: {request.method} {request.url.path} with status {response.status_code} in {duration_ms}ms",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "elapsed_ms": duration_ms,
                "user_id": user_id,
                "company_id": company_id
            }
        )

        # Append Request ID header to response
        response.headers["X-Request-ID"] = request_id
        return response
