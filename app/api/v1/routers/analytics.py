import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import PermissionDeniedException, BusinessRuleException
from app.core.dependencies import get_current_active_user
from app.models.models import User, UserRole
from app.schemas.responses import APIResponse
from app.services.services import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db)


@router.get("/dashboard", response_model=APIResponse[dict])
def get_dashboard_analytics(
    current_user: User = Depends(get_current_active_user),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Retrieves dashboard statistics. Scoped to company for corporate users, global for Admins/Auditors.
    """
    company_id = None
    if current_user.role not in [UserRole.ADMIN, UserRole.AUDITOR]:
        if not current_user.company_id:
            raise PermissionDeniedException("User must belong to a company to access dashboard analytics")
        company_id = current_user.company_id

    from app.services.cache import cache_service
    from app.services.metrics import metrics_service
    
    cache_key = f"analytics:dashboard:company={company_id}"
    cached = cache_service.get(cache_key)
    if cached:
        metrics_service.record_cache_hit()
        return APIResponse(
            success=True,
            message="Dashboard statistics retrieved successfully (cached)",
            data=cached
        )

    metrics_service.record_cache_miss()
    metrics_service.record_db_query()
    
    data = service.get_dashboard(company_id)
    cache_service.set(cache_key, data, ttl=300)
    
    return APIResponse(
        success=True,
        message="Dashboard statistics retrieved successfully",
        data=data
    )


@router.get("/marketplace", response_model=APIResponse[dict])
def get_marketplace_analytics(
    current_user: User = Depends(get_current_active_user),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Retrieves global marketplace volume, listed counts, average pricing, and top registry/projects.
    """
    from app.services.cache import cache_service
    from app.services.metrics import metrics_service
    
    cache_key = "analytics:marketplace"
    cached = cache_service.get(cache_key)
    if cached:
        metrics_service.record_cache_hit()
        return APIResponse(
            success=True,
            message="Marketplace statistics retrieved successfully (cached)",
            data=cached
        )

    metrics_service.record_cache_miss()
    metrics_service.record_db_query()
    
    data = service.get_marketplace_statistics()
    cache_service.set(cache_key, data, ttl=300)
    
    return APIResponse(
        success=True,
        message="Marketplace statistics retrieved successfully",
        data=data
    )


@router.get("/portfolio", response_model=APIResponse[dict])
def get_portfolio_analytics(
    company_id: Optional[uuid.UUID] = Query(None),
    current_user: User = Depends(get_current_active_user),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Retrieves portfolio carbon credit statistics. Scoped to own company for corporate users.
    """
    target_company_id = company_id
    if current_user.role not in [UserRole.ADMIN, UserRole.AUDITOR]:
        if not current_user.company_id:
            raise PermissionDeniedException("User must belong to a company to access portfolio analytics")
        target_company_id = current_user.company_id
    else:
        if not target_company_id:
            raise BusinessRuleException("Admins/Auditors must specify a company_id query parameter")

    from app.services.cache import cache_service
    from app.services.metrics import metrics_service
    
    cache_key = f"analytics:portfolio:company={target_company_id}"
    cached = cache_service.get(cache_key)
    if cached:
        metrics_service.record_cache_hit()
        return APIResponse(
            success=True,
            message="Portfolio statistics retrieved successfully (cached)",
            data=cached
        )

    metrics_service.record_cache_miss()
    metrics_service.record_db_query()
    
    data = service.get_portfolio_statistics(target_company_id)
    cache_service.set(cache_key, data, ttl=300)
    
    return APIResponse(
        success=True,
        message="Portfolio statistics retrieved successfully",
        data=data
    )


@router.get("/retirements", response_model=APIResponse[dict])
def get_retirement_analytics(
    current_user: User = Depends(get_current_active_user),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Retrieves retirement metrics. Scoped to own company for corporate users, global for Admins/Auditors.
    """
    company_id = None
    if current_user.role not in [UserRole.ADMIN, UserRole.AUDITOR]:
        if not current_user.company_id:
            raise PermissionDeniedException("User must belong to a company to access retirement analytics")
        company_id = current_user.company_id

    from app.services.cache import cache_service
    from app.services.metrics import metrics_service
    
    cache_key = f"analytics:retirements:company={company_id}"
    cached = cache_service.get(cache_key)
    if cached:
        metrics_service.record_cache_hit()
        return APIResponse(
            success=True,
            message="Retirement statistics retrieved successfully (cached)",
            data=cached
        )

    metrics_service.record_cache_miss()
    metrics_service.record_db_query()
    
    data = service.get_retirement_statistics(company_id)
    cache_service.set(cache_key, data, ttl=300)
    
    return APIResponse(
        success=True,
        message="Retirement statistics retrieved successfully",
        data=data
    )
