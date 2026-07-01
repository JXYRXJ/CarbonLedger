import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_current_company, get_current_active_user, get_pagination_params, get_service
from app.models.models import User, Company, UserRole, Ownership
from app.schemas.pagination import PaginationParams, PaginatedResponse, PaginationMetadata
from app.schemas.responses import APIResponse
from app.schemas.ownership import OwnershipResponse
from app.repositories.repositories import OwnershipRepository
from app.services.services import OwnershipService
from app.core.exceptions import PermissionDeniedException, NotFoundException

router = APIRouter(prefix="/ownerships", tags=["Holdings & Ownerships"])
company_ownership_router = APIRouter(prefix="/companies", tags=["Holdings & Ownerships"])
batch_ownership_router = APIRouter(prefix="/batches", tags=["Holdings & Ownerships"])


@router.get("", response_model=APIResponse[PaginatedResponse[OwnershipResponse]])
def list_ownerships(
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(get_current_active_user),
    ownership_service: OwnershipService = Depends(get_service(OwnershipService, OwnershipRepository))
) -> APIResponse[PaginatedResponse[OwnershipResponse]]:
    """
    Retrieves a paginated list of all credit holdings on the platform.
    Restricted to ADMIN and AUDITOR roles.
    """
    if current_user.role not in (UserRole.ADMIN, UserRole.AUDITOR):
        raise PermissionDeniedException("Access denied: Insufficient role permissions")
        
    skip = (pagination.page - 1) * pagination.limit
    ownerships = ownership_service.repository.find_many(skip=skip, limit=pagination.limit)
    total = ownership_service.repository.count()
    
    pages = (total + pagination.limit - 1) // pagination.limit if pagination.limit > 0 else 0
    paginated_data = PaginatedResponse(
        items=[OwnershipResponse.model_validate(o) for o in ownerships],
        pagination=PaginationMetadata(
            total=total,
            page=pagination.page,
            limit=pagination.limit,
            pages=pages,
            has_next=pagination.page < pages,
            has_prev=pagination.page > 1
        )
    )
    return APIResponse(
        message="Asset holdings retrieved successfully",
        data=paginated_data
    )


@router.get("/{ownership_id}", response_model=APIResponse[OwnershipResponse])
def get_ownership(
    ownership_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    ownership_service: OwnershipService = Depends(get_service(OwnershipService, OwnershipRepository))
) -> APIResponse[OwnershipResponse]:
    """
    Retrieves detailed records of a specific carbon credit asset holding.
    Accessible to ADMIN/AUDITOR roles, or the company owning the asset holding.
    """
    ownership = ownership_service.repository.find_by_id(ownership_id)
    if not ownership:
        raise NotFoundException(f"Ownership record with ID {ownership_id} not found")
        
    # Assert permissions
    if current_user.role not in (UserRole.ADMIN, UserRole.AUDITOR):
        if not current_user.company_id or current_user.company_id != ownership.company_id:
            raise PermissionDeniedException("Access denied: Insufficient permissions to view this holding")
            
    return APIResponse(
        message="Asset holding details retrieved successfully",
        data=OwnershipResponse.model_validate(ownership)
    )


@company_ownership_router.get("/me/ownerships", response_model=APIResponse[List[OwnershipResponse]])
def list_my_company_ownerships(
    company: Company = Depends(get_current_company),
    current_user: User = Depends(get_current_active_user),
    ownership_service: OwnershipService = Depends(get_service(OwnershipService, OwnershipRepository))
) -> APIResponse[List[OwnershipResponse]]:
    """
    Retrieves carbon credit ownership holdings belonging to the caller's company context.
    Accessible to authenticated users belonging to an active company.
    """
    ownerships = ownership_service.get_company_ownerships(company.id)
    return APIResponse(
        message="Company asset holdings retrieved successfully",
        data=[OwnershipResponse.model_validate(o) for o in ownerships]
    )


@batch_ownership_router.get("/{batch_id}/ownerships", response_model=APIResponse[List[OwnershipResponse]])
def list_batch_ownerships(
    batch_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    ownership_service: OwnershipService = Depends(get_service(OwnershipService, OwnershipRepository))
) -> APIResponse[List[OwnershipResponse]]:
    """
    Retrieves the complete ownership distribution list for a specific credit batch.
    Accessible to all authenticated users.
    """
    ownerships = ownership_service.get_batch_ownerships(batch_id)
    return APIResponse(
        message="Batch ownership distribution retrieved successfully",
        data=[OwnershipResponse.model_validate(o) for o in ownerships]
    )
