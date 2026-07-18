import uuid
from typing import Optional, Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import PermissionDeniedException, BusinessRuleException
from app.core.dependencies import get_current_active_user
from app.models.models import User, UserRole, ListingStatus
from app.schemas.listing import (
    MarketplaceListingResponse,
    MarketplaceListingUpdate
)
from app.schemas.responses import APIResponse
from app.services.services import MarketplaceService
from app.repositories.repositories import MarketplaceRepository
from pydantic import BaseModel, Field

router = APIRouter()


class ListingRequest(BaseModel):
    ownership_id: uuid.UUID
    credits_for_sale: float = Field(..., gt=0.0)
    price_per_credit: float = Field(..., gt=0.0)
    minimum_purchase: float = Field(default=1.0, ge=1.0)
    description: Optional[str] = None
    expires_at: Optional[str] = None


def get_marketplace_service(db: Session = Depends(get_db)) -> MarketplaceService:
    return MarketplaceService(MarketplaceRepository(db))


@router.get("/marketplace", response_model=APIResponse[dict])
def search_marketplace(
    search: Optional[str] = Query(None),
    registry_id: Optional[uuid.UUID] = Query(None),
    country: Optional[str] = Query(None),
    project_type: Optional[str] = Query(None),
    vintage_year: Optional[int] = Query(None),
    verification_standard: Optional[str] = Query(None),
    status: Optional[str] = Query("PUBLISHED"),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    min_credits: Optional[float] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query("newest"),
    db: Session = Depends(get_db),
    service: MarketplaceService = Depends(get_marketplace_service)
):
    """
    Search and filter active marketplace carbon credit listings.
    Supports filtering by Registry, Country, Project Type, Vintage Year, Price Range, and Sorting.
    """
    from app.services.cache import cache_service
    from app.services.metrics import metrics_service
    
    cache_key = f"marketplace:search:search={search}:registry_id={registry_id}:country={country}:project_type={project_type}:vintage_year={vintage_year}:standard={verification_standard}:status={status}:min_price={min_price}:max_price={max_price}:min_credits={min_credits}:skip={skip}:limit={limit}:sort={sort_by}"
    cached = cache_service.get(cache_key)
    if cached:
        metrics_service.record_cache_hit()
        return {
            "success": True,
            "message": "Marketplace listings retrieved successfully (cached)",
            "data": cached
        }

    metrics_service.record_cache_miss()
    metrics_service.record_db_query()
    
    items, total = service.search_marketplace(
        search_query=search,
        registry_id=registry_id,
        country=country,
        project_type=project_type,
        vintage_year=vintage_year,
        verification_standard=verification_standard,
        status=status,
        min_price=min_price,
        max_price=max_price,
        min_credits=min_credits,
        skip=skip,
        limit=limit,
        sort_field=sort_by
    )
    
    data = []
    for item in items:
        # Resolve related models for frontend mapping
        ownership = item.ownership
        batch = ownership.batch if ownership else None
        project = batch.project if batch else None
        seller = item.seller_company
        
        data.append({
            "id": str(item.id),
            "ownership_id": str(item.ownership_id),
            "seller_company_id": str(item.seller_company_id),
            "credits_for_sale": float(item.credits_for_sale),
            "price_per_credit": float(item.price_per_credit),
            "minimum_purchase": float(item.minimum_purchase),
            "description": item.description,
            "status": item.status.value if hasattr(item.status, "value") else item.status,
            "expires_at": item.expires_at.isoformat() if item.expires_at else None,
            "created_at": item.created_at.isoformat(),
            "updated_at": item.updated_at.isoformat(),
            
            # Map camelCase fields for React frontend
            "availableCredits": float(item.credits_for_sale),
            "pricePerCredit": float(item.price_per_credit),
            "verificationStandard": project.verification_standard if project else None,
            "country": project.country if project else None,
            
            # Nested relations
            "batch": {
                "id": str(batch.id) if batch else None,
                "batchNumber": batch.batch_number if batch else None,
                "vintageYear": batch.vintage_year if batch else None,
            } if batch else None,
            "project": {
                "id": str(project.id) if project else None,
                "name": project.name if project else None,
                "country": project.country if project else None,
            } if project else None,
            "seller": {
                "id": str(seller.id) if seller else None,
                "companyName": seller.name if seller else None,
            } if seller else None,
        })
        
    res_data = {
        "items": data,
        "total": total,
        "skip": skip,
        "limit": limit
    }
    
    cache_service.set(cache_key, res_data, ttl=300)
    
    return APIResponse(
        success=True,
        message="Marketplace listings retrieved successfully",
        data=res_data
    )


@router.get("/marketplace/{listing_id}", response_model=APIResponse[dict])
def get_listing_detail(
    listing_id: uuid.UUID,
    service: MarketplaceService = Depends(get_marketplace_service)
):
    """
    Retrieve listing detail records. Open to all users.
    """
    from app.services.cache import cache_service
    from app.services.metrics import metrics_service
    
    cache_key = f"marketplace:id:{listing_id}"
    cached = cache_service.get(cache_key)
    if cached:
        metrics_service.record_cache_hit()
        return {
            "success": True,
            "message": "Listing details retrieved successfully (cached)",
            "data": cached
        }

    metrics_service.record_cache_miss()
    metrics_service.record_db_query()
    
    listing = service.get_listing(listing_id)
    
    # Resolve related models for frontend mapping
    ownership = listing.ownership
    batch = ownership.batch if ownership else None
    project = batch.project if batch else None
    seller = listing.seller_company
    
    data = {
        "id": str(listing.id),
        "ownership_id": str(listing.ownership_id),
        "seller_company_id": str(listing.seller_company_id),
        "credits_for_sale": float(listing.credits_for_sale),
        "price_per_credit": float(listing.price_per_credit),
        "minimum_purchase": float(listing.minimum_purchase),
        "description": listing.description,
        "status": listing.status.value if hasattr(listing.status, "value") else listing.status,
        "expires_at": listing.expires_at.isoformat() if listing.expires_at else None,
        "created_at": listing.created_at.isoformat(),
        "updated_at": listing.updated_at.isoformat(),
        
        # Map camelCase fields for React frontend
        "availableCredits": float(listing.credits_for_sale),
        "pricePerCredit": float(listing.price_per_credit),
        "verificationStandard": project.verification_standard if project else None,
        "country": project.country if project else None,
        
        # Nested relations
        "batch": {
            "id": str(batch.id) if batch else None,
            "batchNumber": batch.batch_number if batch else None,
            "vintageYear": batch.vintage_year if batch else None,
        } if batch else None,
        "project": {
            "id": str(project.id) if project else None,
            "name": project.name if project else None,
            "country": project.country if project else None,
        } if project else None,
        "seller": {
            "id": str(seller.id) if seller else None,
            "companyName": seller.name if seller else None,
        } if seller else None,
    }
    
    return APIResponse(
        success=True,
        message="Listing details retrieved successfully",
        data=data
    )


@router.post("/listings", response_model=APIResponse[dict], status_code=status.HTTP_201_CREATED)
def create_listing(
    payload: ListingRequest,
    current_user: User = Depends(get_current_active_user),
    service: MarketplaceService = Depends(get_marketplace_service)
):
    """
    Create a new listing in PENDING status.
    Permissions: ADMIN, COMPANY_ADMIN, or TRADER only.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.COMPANY_ADMIN, UserRole.TRADER]:
        raise PermissionDeniedException("You do not have permission to create listings")
    if not current_user.company_id:
        raise BusinessRuleException("User must belong to a company to list carbon credits")

    from datetime import datetime
    expires_at = None
    if payload.expires_at:
        try:
            expires_at = datetime.fromisoformat(payload.expires_at.replace("Z", "+00:00"))
        except ValueError:
            raise BusinessRuleException("Invalid ISO format for expires_at")

    from app.services.cache import cache_service
    from app.services.metrics import metrics_service
    
    metrics_service.record_db_query()
    listing = service.create_listing(
        seller_company_id=current_user.company_id,
        data={
            "ownership_id": payload.ownership_id,
            "credits_for_sale": payload.credits_for_sale,
            "price_per_credit": payload.price_per_credit,
            "minimum_purchase": payload.minimum_purchase,
            "description": payload.description,
            "expires_at": expires_at
        },
        user_id=current_user.id
    )
    
    # Invalidate cache
    cache_service.invalidate_pattern("marketplace:*")
    cache_service.invalidate_pattern("analytics:*")
    
    return APIResponse(
        success=True,
        message="Listing created successfully in PENDING status",
        data={
            "id": str(listing.id),
            "status": listing.status,
            "credits_for_sale": float(listing.credits_for_sale),
            "price_per_credit": float(listing.price_per_credit)
        }
    )


@router.patch("/listings/{listing_id}", response_model=APIResponse[dict])
def update_listing(
    listing_id: uuid.UUID,
    payload: MarketplaceListingUpdate,
    current_user: User = Depends(get_current_active_user),
    service: MarketplaceService = Depends(get_marketplace_service)
):
    """
    Update details of a carbon credit listing.
    Permissions: COMPANY_ADMIN (for their company) or ADMIN only.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.COMPANY_ADMIN]:
        raise PermissionDeniedException("You do not have permission to update listings")
    if not current_user.company_id and current_user.role != UserRole.ADMIN:
        raise PermissionDeniedException("User must belong to a company to update listings")

    comp_id = current_user.company_id or uuid.uuid4()
    if current_user.role == UserRole.ADMIN:
        existing = service.get_listing(listing_id)
        comp_id = existing.seller_company_id

    from app.services.cache import cache_service
    from app.services.metrics import metrics_service
    
    metrics_service.record_db_query()
    updated = service.update_listing(
        listing_id=listing_id,
        data=payload.model_dump(exclude_unset=True),
        company_id=comp_id,
        user_id=current_user.id
    )
    
    # Invalidate cache
    cache_service.invalidate_pattern("marketplace:*")
    cache_service.invalidate_pattern("analytics:*")
    
    return APIResponse(
        success=True,
        message="Listing updated successfully",
        data={
            "id": str(updated.id),
            "status": updated.status,
            "credits_for_sale": float(updated.credits_for_sale)
        }
    )


@router.delete("/listings/{listing_id}", response_model=APIResponse[dict])
def delete_listing(
    listing_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    service: MarketplaceService = Depends(get_marketplace_service)
):
    """
    Cancel and soft-delete an existing listing.
    Permissions: COMPANY_ADMIN (for their company) or ADMIN only.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.COMPANY_ADMIN]:
        raise PermissionDeniedException("You do not have permission to delete listings")
    if not current_user.company_id and current_user.role != UserRole.ADMIN:
        raise PermissionDeniedException("User must belong to a company to delete listings")

    comp_id = current_user.company_id or uuid.uuid4()
    if current_user.role == UserRole.ADMIN:
        existing = service.get_listing(listing_id)
        comp_id = existing.seller_company_id

    from app.services.cache import cache_service
    from app.services.metrics import metrics_service
    
    metrics_service.record_db_query()
    service.delete_listing(listing_id, comp_id, current_user.id)
    
    # Invalidate cache
    cache_service.invalidate_pattern("marketplace:*")
    cache_service.invalidate_pattern("analytics:*")
    
    return APIResponse(
        success=True,
        message="Listing deleted successfully",
        data={}
    )


@router.post("/admin/listings/{listing_id}/approve", response_model=APIResponse[dict])
def approve_listing(
    listing_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    service: MarketplaceService = Depends(get_marketplace_service)
):
    """
    Approve a pending listing. Sets status to APPROVED.
    Permissions: ADMIN only.
    """
    if current_user.role != UserRole.ADMIN:
        raise PermissionDeniedException("Only administrators can approve listings")
        
    from app.services.cache import cache_service
    from app.services.metrics import metrics_service
    
    metrics_service.record_db_query()
    listing = service.approve_listing(listing_id, current_user.id)
    listing = service.publish_listing(listing_id, current_user.id)
    
    # Invalidate cache
    cache_service.invalidate_pattern("marketplace:*")
    cache_service.invalidate_pattern("analytics:*")
    
    return APIResponse(
        success=True,
        message="Listing approved and published to the marketplace",
        data={
            "id": str(listing.id),
            "status": listing.status
        }
    )


@router.post("/admin/listings/{listing_id}/reject", response_model=APIResponse[dict])
def reject_listing(
    listing_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    service: MarketplaceService = Depends(get_marketplace_service)
):
    """
    Reject a pending listing. Sets status to REJECTED.
    Permissions: ADMIN only.
    """
    if current_user.role != UserRole.ADMIN:
        raise PermissionDeniedException("Only administrators can reject listings")
        
    from app.services.cache import cache_service
    from app.services.metrics import metrics_service
    
    metrics_service.record_db_query()
    listing = service.reject_listing(listing_id, current_user.id)
    
    # Invalidate cache
    cache_service.invalidate_pattern("marketplace:*")
    cache_service.invalidate_pattern("analytics:*")
    
    return APIResponse(
        success=True,
        message="Listing rejected successfully",
        data={
            "id": str(listing.id),
            "status": listing.status
        }
    )
