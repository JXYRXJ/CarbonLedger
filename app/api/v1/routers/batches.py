import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_current_admin, get_current_active_user, get_pagination_params, get_service
from app.models.models import User, CreditBatch
from app.schemas.pagination import PaginationParams, PaginatedResponse, PaginationMetadata
from app.schemas.responses import APIResponse
from app.schemas.batch import CreditBatchCreate, CreditBatchUpdate, CreditBatchResponse
from app.schemas.project import CarbonProjectResponse
from app.schemas.registry import RegistryResponse
from app.repositories.repositories import BatchRepository, ProjectRepository, RegistryRepository, OwnershipRepository, CompanyRepository
from app.services.services import BatchService, ProjectService, RegistryService, OwnershipService, CompanyService

router = APIRouter(prefix="/batches", tags=["Credit Batches"])


@router.get("", response_model=APIResponse[PaginatedResponse[CreditBatchResponse]])
def list_batches(
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(get_current_active_user),
    batch_service: BatchService = Depends(get_service(BatchService, BatchRepository))
) -> APIResponse[PaginatedResponse[CreditBatchResponse]]:
    """
    Retrieves a paginated list of carbon credit batches issued on the platform.
    Supports query filters, search strings, sorting, and pagination.
    Accessible to all authenticated users.
    """
    from app.services.cache import cache_service
    from app.services.metrics import metrics_service
    
    cache_key = f"batches:all:search={pagination.search}:page={pagination.page}:limit={pagination.limit}:sort={pagination.sort}:order={pagination.order}"
    cached = cache_service.get(cache_key)
    if cached:
        metrics_service.record_cache_hit()
        return APIResponse(
            message="Batches retrieved successfully (cached)",
            data=PaginatedResponse.model_validate(cached)
        )

    metrics_service.record_cache_miss()
    metrics_service.record_db_query()
    
    batches, total = batch_service.search_batches(
        search_query=pagination.search,
        page=pagination.page,
        limit=pagination.limit,
        sort=pagination.sort,
        order=pagination.order
    )
    
    pages = (total + pagination.limit - 1) // pagination.limit if pagination.limit > 0 else 0
    paginated_data = PaginatedResponse(
        items=[CreditBatchResponse.model_validate(b) for b in batches],
        pagination=PaginationMetadata(
            total=total,
            page=pagination.page,
            limit=pagination.limit,
            pages=pages,
            has_next=pagination.page < pages,
            has_prev=pagination.page > 1
        )
    )
    
    cache_service.set(cache_key, paginated_data.model_dump(mode="json"), ttl=300)
    
    return APIResponse(
        message="Batches retrieved successfully",
        data=paginated_data
    )


@router.get("/{batch_id}", response_model=APIResponse[dict])
def get_batch_details(
    batch_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    batch_service: BatchService = Depends(get_service(BatchService, BatchRepository)),
    project_service: ProjectService = Depends(get_service(ProjectService, ProjectRepository)),
    registry_service: RegistryService = Depends(get_service(RegistryService, RegistryRepository)),
    ownership_service: OwnershipService = Depends(get_service(OwnershipService, OwnershipRepository)),
    company_service: CompanyService = Depends(get_service(CompanyService, CompanyRepository))
) -> APIResponse[dict]:
    """
    Retrieves a unified view of a carbon credit batch including its associated
    Project profile, Registry metadata, current Status, and Ownership distribution.
    Accessible to all authenticated users.
    """
    from app.services.cache import cache_service
    from app.services.metrics import metrics_service
    
    cache_key = f"batches:id:{batch_id}"
    cached = cache_service.get(cache_key)
    if cached:
        metrics_service.record_cache_hit()
        return APIResponse(
            message="Batch details retrieved successfully (cached)",
            data=cached
        )

    metrics_service.record_cache_miss()
    metrics_service.record_db_query()
    
    batch = batch_service.get_batch(batch_id)
    project = project_service.get_project(batch.project_id)
    registry = registry_service.get_registry(project.registry_id)
    ownerships = ownership_service.get_batch_ownerships(batch_id)
    stats = batch_service.get_batch_statistics(batch_id)

    ownership_dist = []
    for own in ownerships:
        comp = company_service.repository.find_by_id(own.company_id)
        ownership_dist.append({
            "ownership_id": str(own.id),
            "company_id": str(own.company_id),
            "company_name": comp.name if comp else "Unknown Company",
            "owned_credits": float(own.owned_credits),
            "percentage": (float(own.owned_credits) / float(batch.total_credits) * 100.0) if batch.total_credits > 0 else 0.0,
            "average_purchase_price": float(own.average_purchase_price)
        })

    data = {
        "batch": CreditBatchResponse.model_validate(batch).model_dump(),
        "project": CarbonProjectResponse.model_validate(project).model_dump(),
        "registry": RegistryResponse.model_validate(registry).model_dump(),
        "ownership_distribution": ownership_dist,
        "current_status": batch.status,
        "statistics": stats
    }
    
    cache_service.set(cache_key, data, ttl=300)
    
    return APIResponse(
        message="Batch details retrieved successfully",
        data=data
    )


@router.post("", response_model=APIResponse[CreditBatchResponse], status_code=status.HTTP_201_CREATED)
def create_batch(
    payload: CreditBatchCreate,
    admin_user: User = Depends(get_current_admin),
    batch_service: BatchService = Depends(get_service(BatchService, BatchRepository))
) -> APIResponse[CreditBatchResponse]:
    """
    Issues a new carbon credit batch under a verified Carbon Project.
    Can optionally assign the initial ownership to a company developer via 'company_id'.
    Restricted to ADMIN users.
    """
    from app.services.cache import cache_service
    from app.services.metrics import metrics_service
    
    metrics_service.record_db_query()
    new_batch = batch_service.create_batch(payload.model_dump(), admin_user.id)
    
    # Invalidate cache
    cache_service.invalidate_pattern("batches:*")
    cache_service.invalidate_pattern("analytics:*")
    
    return APIResponse(
        message="Carbon credit batch issued successfully",
        data=CreditBatchResponse.model_validate(new_batch)
    )


@router.patch("/{batch_id}", response_model=APIResponse[CreditBatchResponse])
def update_batch(
    batch_id: uuid.UUID,
    payload: CreditBatchUpdate,
    admin_user: User = Depends(get_current_admin),
    batch_service: BatchService = Depends(get_service(BatchService, BatchRepository))
) -> APIResponse[CreditBatchResponse]:
    """
    Updates the Status or Metadata attributes of an existing credit batch.
    Validates status transitions to ensure immutability is respected.
    Restricted to ADMIN users.
    """
    from app.services.cache import cache_service
    from app.services.metrics import metrics_service
    
    metrics_service.record_db_query()
    updated = batch_service.update_batch(batch_id, payload.model_dump(exclude_unset=True), admin_user.id)
    
    # Invalidate cache
    cache_service.invalidate_pattern("batches:*")
    cache_service.invalidate_pattern("analytics:*")
    
    return APIResponse(
        message="Carbon credit batch status/metadata updated successfully",
        data=CreditBatchResponse.model_validate(updated)
    )


@router.get("/{batch_id}/statistics", response_model=APIResponse[dict])
def get_batch_statistics(
    batch_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    batch_service: BatchService = Depends(get_service(BatchService, BatchRepository))
) -> APIResponse[dict]:
    """
    Retrieves statistics (total, remaining, retired, unique owners count) for a credit batch.
    Accessible to all authenticated users.
    """
    from app.services.cache import cache_service
    from app.services.metrics import metrics_service
    
    cache_key = f"batches:stats:{batch_id}"
    cached = cache_service.get(cache_key)
    if cached:
        metrics_service.record_cache_hit()
        return APIResponse(
            message="Batch statistics generated successfully (cached)",
            data=cached
        )

    metrics_service.record_cache_miss()
    metrics_service.record_db_query()
    
    stats = batch_service.get_batch_statistics(batch_id)
    
    cache_service.set(cache_key, stats, ttl=300)
    
    return APIResponse(
        message="Batch statistics generated successfully",
        data=stats
    )
