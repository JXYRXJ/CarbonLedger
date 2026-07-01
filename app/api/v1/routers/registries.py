import uuid
from typing import Optional
from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_current_admin, get_current_active_user, get_pagination_params, get_service
from app.models.models import User, Registry
from app.schemas.pagination import PaginationParams, PaginatedResponse, PaginationMetadata
from app.schemas.responses import APIResponse
from app.schemas.registry import RegistryCreate, RegistryUpdate, RegistryResponse
from app.repositories.repositories import RegistryRepository
from app.services.services import RegistryService
from app.services.cache import cache_service
from app.services.metrics import metrics_service

router = APIRouter(prefix="/registries", tags=["Registries"])


@router.get("", response_model=APIResponse[PaginatedResponse[RegistryResponse]])
def list_registries(
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(get_current_active_user),
    registry_service: RegistryService = Depends(get_service(RegistryService, RegistryRepository))
) -> APIResponse[PaginatedResponse[RegistryResponse]]:
    """
    Retrieves a paginated, sorted, and filtered list of supported carbon standard registries.
    Accessible to all authenticated users.
    """
    cache_key = f"registries:all:search={pagination.search}:page={pagination.page}:limit={pagination.limit}:sort={pagination.sort}:order={pagination.order}"
    
    cached = cache_service.get(cache_key)
    if cached:
        metrics_service.record_cache_hit()
        return APIResponse(
            message="Registries retrieved successfully (cached)",
            data=PaginatedResponse.model_validate(cached)
        )

    metrics_service.record_cache_miss()
    metrics_service.record_db_query()
    
    registries, total = registry_service.search_registries(
        search_query=pagination.search,
        status=None,
        country=None,
        accreditation=None,
        page=pagination.page,
        limit=pagination.limit,
        sort=pagination.sort,
        order=pagination.order
    )
    
    pages = (total + pagination.limit - 1) // pagination.limit if pagination.limit > 0 else 0
    paginated_data = PaginatedResponse(
        items=[RegistryResponse.model_validate(r) for r in registries],
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
        message="Registries retrieved successfully",
        data=paginated_data
    )


@router.get("/{registry_id}", response_model=APIResponse[RegistryResponse])
def get_registry(
    registry_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    registry_service: RegistryService = Depends(get_service(RegistryService, RegistryRepository))
) -> APIResponse[RegistryResponse]:
    """
    Retrieves information on a specific registry by its unique UUID.
    Accessible to all authenticated users.
    """
    cache_key = f"registries:id:{registry_id}"
    cached = cache_service.get(cache_key)
    if cached:
        metrics_service.record_cache_hit()
        return APIResponse(
            message="Registry details retrieved successfully (cached)",
            data=RegistryResponse.model_validate(cached)
        )

    metrics_service.record_cache_miss()
    metrics_service.record_db_query()
    
    registry = registry_service.get_registry(registry_id)
    resp_data = RegistryResponse.model_validate(registry)
    
    cache_service.set(cache_key, resp_data.model_dump(), ttl=300)
    
    return APIResponse(
        message="Registry details retrieved successfully",
        data=resp_data
    )


@router.post("", response_model=APIResponse[RegistryResponse], status_code=status.HTTP_201_CREATED)
def create_registry(
    payload: RegistryCreate,
    admin_user: User = Depends(get_current_admin),
    registry_service: RegistryService = Depends(get_service(RegistryService, RegistryRepository))
) -> APIResponse[RegistryResponse]:
    """
    Creates a new carbon standard registry. Restricted to ADMIN users.
    """
    metrics_service.record_db_query()
    new_reg = registry_service.create_registry(payload.model_dump(), admin_user.id)
    
    # Invalidate cache
    cache_service.invalidate_pattern("registries:*")
    cache_service.invalidate_pattern("analytics:*")
    
    return APIResponse(
        message="Registry created successfully",
        data=RegistryResponse.model_validate(new_reg)
    )


@router.patch("/{registry_id}", response_model=APIResponse[RegistryResponse])
def update_registry(
    registry_id: uuid.UUID,
    payload: RegistryUpdate,
    admin_user: User = Depends(get_current_admin),
    registry_service: RegistryService = Depends(get_service(RegistryService, RegistryRepository))
) -> APIResponse[RegistryResponse]:
    """
    Updates general metadata attributes of a registry. Restricted to ADMIN users.
    """
    metrics_service.record_db_query()
    updated = registry_service.update_registry(registry_id, payload.model_dump(exclude_unset=True), admin_user.id)
    
    # Invalidate cache
    cache_service.invalidate_pattern("registries:*")
    cache_service.invalidate_pattern("analytics:*")
    
    return APIResponse(
        message="Registry updated successfully",
        data=RegistryResponse.model_validate(updated)
    )


@router.delete("/{registry_id}", response_model=APIResponse[RegistryResponse])
def delete_registry(
    registry_id: uuid.UUID,
    admin_user: User = Depends(get_current_admin),
    registry_service: RegistryService = Depends(get_service(RegistryService, RegistryRepository))
) -> APIResponse[RegistryResponse]:
    """
    Soft deletes a registry. Restricted to ADMIN users.
    """
    metrics_service.record_db_query()
    deleted = registry_service.delete_registry(registry_id, admin_user.id)
    
    # Invalidate cache
    cache_service.invalidate_pattern("registries:*")
    cache_service.invalidate_pattern("analytics:*")
    
    return APIResponse(
        message="Registry successfully soft deleted",
        data=RegistryResponse.model_validate(deleted)
    )


@router.get("/{registry_id}/statistics", response_model=APIResponse[dict])
def get_registry_statistics(
    registry_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    registry_service: RegistryService = Depends(get_service(RegistryService, RegistryRepository))
) -> APIResponse[dict]:
    """
    Aggregates project counts and issued credits statistics for a specific registry.
    Accessible to all authenticated users.
    """
    cache_key = f"registries:stats:{registry_id}"
    cached = cache_service.get(cache_key)
    if cached:
        metrics_service.record_cache_hit()
        return APIResponse(
            message="Registry statistics generated successfully (cached)",
            data=cached
        )

    metrics_service.record_cache_miss()
    metrics_service.record_db_query()
    
    stats = registry_service.get_registry_statistics(registry_id)
    
    cache_service.set(cache_key, stats, ttl=300)
    
    return APIResponse(
        message="Registry statistics generated successfully",
        data=stats
    )
