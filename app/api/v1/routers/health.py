import time
from datetime import datetime, timezone
from fastapi import APIRouter, status, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db, check_db_health
from app.schemas.responses import APIResponse
from app.services.cache import cache_service

router = APIRouter(tags=["Health"])

# Record application startup time for uptime calculations
START_TIME = time.time()


@router.get("/health", response_model=APIResponse[dict])
def health_check(db: Session = Depends(get_db)) -> APIResponse[dict]:
    """
    Performs overall system liveness, database connection, cache connection, and blockchain health checks.
    """
    db_ok = check_db_health()
    
    # Check cache status
    cache_ok = True
    if cache_service.redis_client:
        try:
            cache_service.redis_client.ping()
        except Exception:
            cache_ok = False
            
    # Check blockchain status
    from app.blockchain.service import BlockchainService
    b_service = BlockchainService()
    b_health = b_service.health_check()
    b_ok = not settings.BLOCKCHAIN_ENABLED or b_health.get("blockchain_connected", False)

    overall_ok = db_ok and cache_ok and b_ok
    status_str = "healthy" if overall_ok else "degraded"
    
    data = {
        "status": status_str,
        "database": "connected" if db_ok else "disconnected",
        "cache": "connected" if cache_ok else "degraded (in-memory fallback)",
        "blockchain": b_health,
        "environment": settings.ENVIRONMENT,
        "version": settings.VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_sec": int(time.time() - START_TIME)
    }

    return APIResponse(
        success=overall_ok,
        message="System is healthy" if overall_ok else "One or more dependencies are degraded",
        data=data
    )


@router.get("/health/database", response_model=APIResponse[dict])
def database_health_check() -> APIResponse[dict]:
    """
    Dedicated database connection readiness health check.
    """
    db_ok = check_db_health()
    return APIResponse(
        success=db_ok,
        message="Database connection check succeeded" if db_ok else "Database connectivity check failed",
        data={
            "database": "connected" if db_ok else "disconnected",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


@router.get("/health/cache", response_model=APIResponse[dict])
def cache_health_check() -> APIResponse[dict]:
    """
    Dedicated Redis caching connection health check.
    """
    cache_ok = True
    cache_type = "redis"
    if cache_service.redis_client:
        try:
            cache_service.redis_client.ping()
        except Exception:
            cache_ok = False
            cache_type = "in-memory fallback (redis connection failed)"
    else:
        cache_type = "in-memory fallback (not configured)"

    return APIResponse(
        success=cache_ok,
        message="Cache connection check succeeded" if cache_ok else "Cache is operating in degraded/fallback state",
        data={
            "cache_type": cache_type,
            "status": "connected" if cache_ok and cache_service.redis_client else "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


@router.get("/health/application", response_model=APIResponse[dict])
def application_health_check() -> APIResponse[dict]:
    """
    Dedicated application metadata, environment, and uptime health check.
    """
    return APIResponse(
        success=True,
        message="Application is running",
        data={
            "status": "healthy",
            "environment": settings.ENVIRONMENT,
            "version": settings.VERSION,
            "uptime_sec": int(time.time() - START_TIME),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )
