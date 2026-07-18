import uuid
from typing import Optional, Any
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


@router.get("", response_model=APIResponse[PaginatedResponse[Any]])
def list_registries(
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(get_current_active_user),
    registry_service: RegistryService = Depends(get_service(RegistryService, RegistryRepository))
):
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
    
    items_data = []
    for r in registries:
        items_data.append({
            "id": str(r.id),
            "name": r.name,
            "country": r.country,
            "website": r.website,
            "accreditation": r.accreditation,
            "description": r.description,
            "status": r.status,
            "created_at": r.created_at.isoformat(),
            "updated_at": r.updated_at.isoformat(),
            
            # camelCase mappings
            "projectsCount": len(r.projects) if r.projects else 0,
        })
    
    pages = (total + pagination.limit - 1) // pagination.limit if pagination.limit > 0 else 0
    paginated_data = PaginatedResponse(
        items=items_data,
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


@router.get("/{registry_id}", response_model=APIResponse[dict])
def get_registry(
    registry_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    registry_service: RegistryService = Depends(get_service(RegistryService, RegistryRepository))
) -> APIResponse[dict]:
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
            data=cached
        )

    metrics_service.record_cache_miss()
    metrics_service.record_db_query()
    
    registry = registry_service.get_registry(registry_id)
    stats = registry_service.get_registry_statistics(registry_id)
    
    projects_data = []
    for p in registry.projects:
        if p.deleted_at is None:
            projects_data.append({
                "id": str(p.id),
                "registry_id": str(p.registry_id),
                "project_code": p.project_code,
                "name": p.name,
                "country": p.country,
                "project_type": p.project_type,
                "verification_standard": p.verification_standard,
                "methodology": p.methodology,
                "description": p.description,
                "developer": p.developer,
                "start_date": p.start_date.isoformat() if p.start_date else None,
                "end_date": p.end_date.isoformat() if p.end_date else None,
                
                # camelCase
                "projectType": p.project_type,
                "verificationStandard": p.verification_standard,
                "registryName": registry.name,
            })

    data = {
        "id": str(registry.id),
        "name": registry.name,
        "country": registry.country,
        "website": registry.website,
        "accreditation": registry.accreditation,
        "description": registry.description,
        "status": registry.status,
        "created_at": registry.created_at.isoformat(),
        "updated_at": registry.updated_at.isoformat(),
        
        # camelCase
        "projectsCount": stats["projects_count"],
        
        # Nested relations
        "projects": projects_data,
        
        # Detailed stats block
        "stats": {
            "total_credits_issued": float(stats["total_credits_issued"]),
            "batches_count": int(stats["batches_count"]),
            "active_projects": int(stats["active_projects"]),
            "inactive_projects": int(stats["inactive_projects"]),
        }
    }
    
    cache_service.set(cache_key, data, ttl=300)
    
    return APIResponse(
        message="Registry details retrieved successfully",
        data=data
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
