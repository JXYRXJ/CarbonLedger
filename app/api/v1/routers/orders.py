import uuid
from typing import Optional, Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import PermissionDeniedException, BusinessRuleException
from app.core.dependencies import get_current_active_user
from app.models.models import User, UserRole, PurchaseOrderStatus
from app.schemas.responses import APIResponse
from app.services.services import OrderService
from app.repositories.repositories import OrderRepository
from pydantic import BaseModel, Field

router = APIRouter()


class OrderCreateRequest(BaseModel):
    listing_id: uuid.UUID
    requested_credits: float = Field(..., gt=0.0)


def get_order_service(db: Session = Depends(get_db)) -> OrderService:
    return OrderService(OrderRepository(db))


@router.post("/orders", response_model=APIResponse[dict], status_code=status.HTTP_201_CREATED)
def create_purchase_order(
    payload: OrderCreateRequest,
    current_user: User = Depends(get_current_active_user),
    service: OrderService = Depends(get_order_service)
):
    """
    Submit a purchase order to purchase carbon credits from a published listing.
    Permissions: ADMIN, COMPANY_ADMIN, or TRADER only.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.COMPANY_ADMIN, UserRole.TRADER]:
        raise PermissionDeniedException("You do not have permission to purchase carbon credits")
    if not current_user.company_id:
        raise BusinessRuleException("User must belong to a company to place purchase orders")

    from app.services.cache import cache_service
    from app.services.metrics import metrics_service
    
    metrics_service.record_db_query()
    order = service.create_order(
        buyer_company_id=current_user.company_id,
        data={
            "listing_id": payload.listing_id,
            "requested_credits": payload.requested_credits
        },
        user_id=current_user.id
    )

    # Invalidate cache
    cache_service.invalidate_pattern("marketplace:*")
    cache_service.invalidate_pattern("analytics:*")
    cache_service.invalidate_pattern("batches:*")
    cache_service.invalidate_pattern("projects:*")

    return APIResponse(
        success=True,
        message="Carbon credit purchase completed successfully",
        data={
            "id": str(order.id),
            "listing_id": str(order.listing_id),
            "requested_credits": float(order.requested_credits),
            "price_per_credit": float(order.price_per_credit),
            "total_price": float(order.total_price),
            "status": order.status
        }
    )


@router.get("/orders", response_model=APIResponse[list])
def list_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    service: OrderService = Depends(get_order_service)
):
    """
    List orders.
    Auditors and Admins can view all orders.
    Corporate users can view orders placed by their company.
    """
    if current_user.role in [UserRole.ADMIN, UserRole.AUDITOR]:
        orders = service.list_orders()
    else:
        if not current_user.company_id:
            raise PermissionDeniedException("User has no associated company")
        orders = service.list_orders(buyer_company_id=current_user.company_id)

    data = []
    for order in orders:
        data.append({
            "id": str(order.id),
            "listing_id": str(order.listing_id),
            "buyer_company_id": str(order.buyer_company_id),
            "requested_credits": float(order.requested_credits),
            "price_per_credit": float(order.price_per_credit),
            "total_price": float(order.total_price),
            "status": order.status,
            "payment_reference": order.payment_reference,
            "created_at": order.created_at.isoformat(),
            "updated_at": order.updated_at.isoformat()
        })

    return APIResponse(
        success=True,
        message="Orders retrieved successfully",
        data=data
    )


@router.get("/orders/{order_id}", response_model=APIResponse[dict])
def get_order_details(
    order_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    service: OrderService = Depends(get_order_service)
):
    """
    Retrieve details of a specific purchase order.
    Permissions: Admin, Auditor, or Owner (buyer company).
    """
    order = service.get_order(order_id)
    
    if current_user.role not in [UserRole.ADMIN, UserRole.AUDITOR]:
        if order.buyer_company_id != current_user.company_id:
            raise PermissionDeniedException("You do not have permission to view this order")

    return APIResponse(
        success=True,
        message="Order details retrieved successfully",
        data={
            "id": str(order.id),
            "listing_id": str(order.listing_id),
            "buyer_company_id": str(order.buyer_company_id),
            "requested_credits": float(order.requested_credits),
            "price_per_credit": float(order.price_per_credit),
            "total_price": float(order.total_price),
            "status": order.status,
            "payment_reference": order.payment_reference,
            "created_at": order.created_at.isoformat(),
            "updated_at": order.updated_at.isoformat()
        }
    )


@router.patch("/orders/{order_id}/cancel", response_model=APIResponse[dict])
def cancel_purchase_order(
    order_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    service: OrderService = Depends(get_order_service)
):
    """
    Cancel a pending or processing purchase order.
    Permissions: Owner (buyer company) only.
    """
    if not current_user.company_id:
        raise PermissionDeniedException("User must belong to a company to cancel orders")

    order = service.cancel_order(order_id, current_user.company_id, current_user.id)
    return APIResponse(
        success=True,
        message="Order cancelled successfully",
        data={
            "id": str(order.id),
            "status": order.status
        }
    )
