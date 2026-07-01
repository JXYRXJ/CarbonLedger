from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import settings
from app.core.logging import configure_logging
from app.core.exceptions import register_exception_handlers
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.middleware.security_middleware import SecurityHeadersMiddleware
from app.middleware.size_limit import ContentLengthLimitMiddleware
from app.middleware.rate_limit import RateLimitingMiddleware
from app.api.v1.routers import routers_list


def create_app() -> FastAPI:
    """
    Application factory to configure and return the FastAPI application instance.
    """
    # Initialize logger configuration
    configure_logging()

    # Create FastAPI instance with custom metadata
    app = FastAPI(
        title="CarbonLedger API",
        version="1.0.0",
        description="Enterprise Carbon Asset Management Platform API",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/api/v1/openapi.json"
    )

    # 1. CORS Middleware
    # Configure allowed origins including localhost, Vercel frontend, and configured URLs
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Length", "X-Request-ID"]
    )

    # 2. GZip Compression Middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # 3. Security Headers Middleware (OWASP alignment)
    app.add_middleware(SecurityHeadersMiddleware)

    # 3.5. Security Limits (Size limit and Rate limiting)
    app.add_middleware(ContentLengthLimitMiddleware)
    app.add_middleware(RateLimitingMiddleware, requests_limit=100, window_sec=60)

    # 4. Request Logging & Timing Middleware
    app.add_middleware(RequestLoggingMiddleware)

    # 5. Trusted Host Middleware
    # Allow local connections and Render dynamic hosts
    allowed_hosts = ["localhost", "127.0.0.1"]
    if settings.is_production:
        # In production on Render/Vercel, we can whitelist wildcard subdomains or specific external URLs
        # Render specifies RENDER_EXTERNAL_URL which we add to our configuration
        if settings.RENDER_EXTERNAL_URL:
            # Strip scheme if present
            host = settings.RENDER_EXTERNAL_URL.replace("https://", "").replace("http://", "").split("/")[0]
            allowed_hosts.append(host)
        else:
            # Fallback for dynamic host environments
            allowed_hosts.append("*")
    else:
        # Allow all hosts during local development/testing
        allowed_hosts.append("*")

    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

    # 6. Global exception handlers
    register_exception_handlers(app)

    # 7. Include API V1 routers under /api/v1 prefix
    for router, prefix in routers_list:
        app.include_router(
            router,
            prefix=f"{settings.API_V1_STR}{prefix}"
        )

    return app


# Expose application instance for Uvicorn startup
app = create_app()
