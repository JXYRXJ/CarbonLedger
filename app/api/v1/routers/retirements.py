import uuid
from typing import Optional, Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.exceptions import PermissionDeniedException, BusinessRuleException
from app.core.dependencies import get_current_active_user, get_pagination_params
from app.schemas.pagination import PaginationParams
from app.schemas.responses import APIResponse
from app.models.models import User, UserRole, Retirement
from app.services.services import RetirementService
from app.repositories.repositories import RetirementRepository

router = APIRouter(prefix="/retirements", tags=["Retirements"])


class RetireCreditsRequest(BaseModel):
    ownership_id: uuid.UUID
    quantity: float = Field(..., gt=0.0)
    beneficiary_name: str = Field(..., example="Acme Corporation")
    retirement_reason: str = Field(..., example="Offsetting Q2 2026 Scope 1 Emissions")
    signature: Optional[str] = Field(None, example="0xabc123...signature")


def get_retirement_service(db: Session = Depends(get_db)) -> RetirementService:
    return RetirementService(RetirementRepository(db))


@router.post("", response_model=APIResponse[dict], status_code=status.HTTP_201_CREATED)
def execute_retirement(
    payload: RetireCreditsRequest,
    current_user: User = Depends(get_current_active_user),
    service: RetirementService = Depends(get_retirement_service)
):
    """
    Executes a carbon credit retirement operation. Permanent removal of credits from ownership.
    """
    if not current_user.company_id:
        raise BusinessRuleException("User must belong to a company to retire carbon credits")
    if current_user.role not in [UserRole.ADMIN, UserRole.COMPANY_ADMIN, UserRole.TRADER]:
        raise PermissionDeniedException("You do not have permission to retire credits")

    from app.services.cache import cache_service
    from app.services.metrics import metrics_service
    
    metrics_service.record_db_query()
    retirement = service.retire_credits(
        company_id=current_user.company_id,
        user_id=current_user.id,
        ownership_id=payload.ownership_id,
        quantity=payload.quantity,
        beneficiary_name=payload.beneficiary_name,
        reason=payload.retirement_reason
    )
    
    # Invalidate cache
    cache_service.invalidate_pattern("analytics:*")
    cache_service.invalidate_pattern("batches:*")
    cache_service.invalidate_pattern("projects:*")
    
    return APIResponse(
        success=True,
        message="Carbon credits retired successfully",
        data={
            "id": str(retirement.id),
            "certificate_number": retirement.certificate_number,
            "credits_retired": float(retirement.credits_retired),
            "status": "VERIFIED",
            "retired_at": retirement.retired_at.isoformat()
        }
    )


@router.get("", response_model=APIResponse[dict])
def list_retirements(
    cert_number: Optional[str] = Query(None),
    batch_number: Optional[str] = Query(None),
    company_name: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(get_current_active_user),
    service: RetirementService = Depends(get_retirement_service)
):
    """
    Retrieves carbon credit retirement records. Scoped to own company for corporate users.
    """
    from datetime import datetime
    s_date = None
    e_date = None
    if start_date:
        try:
            s_date = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        except ValueError:
            raise BusinessRuleException("Invalid start_date format")
    if end_date:
        try:
            e_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        except ValueError:
            raise BusinessRuleException("Invalid end_date format")

    if current_user.role in [UserRole.ADMIN, UserRole.AUDITOR]:
        retirements = service.repository.search(
            cert_number=cert_number,
            batch_number=batch_number,
            company_name=company_name,
            start_date=s_date,
            end_date=e_date
        )
    else:
        if not current_user.company_id:
            raise PermissionDeniedException("User must belong to a company to list retirements")
        retirements = service.list_retirements(company_id=current_user.company_id)

    # Manual slicing for pagination
    total = len(retirements)
    start_idx = (pagination.page - 1) * pagination.limit
    end_idx = start_idx + pagination.limit
    sliced = retirements[start_idx:end_idx]

    data = []
    for ret in sliced:
        data.append({
            "id": str(ret.id),
            "ownership_id": str(ret.ownership_id),
            "company_id": str(ret.company_id),
            "company_name": ret.company.name if ret.company else None,
            "credits_retired": float(ret.credits_retired),
            "reason": ret.reason,
            "certificate_number": ret.certificate_number,
            "blockchain_tx_hash": ret.blockchain_tx_hash,
            "retired_at": ret.retired_at.isoformat()
        })

    return APIResponse(
        success=True,
        message="Retirements list retrieved successfully",
        data={
            "items": data,
            "total": total,
            "page": pagination.page,
            "limit": pagination.limit
        }
    )


@router.get("/{retirement_id}", response_model=APIResponse[dict])
def get_retirement_detail(
    retirement_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    service: RetirementService = Depends(get_retirement_service)
):
    """
    Retrieves details for a specific carbon asset retirement record.
    """
    ret = service.get_retirement(retirement_id)
    if current_user.role not in [UserRole.ADMIN, UserRole.AUDITOR]:
        if ret.company_id != current_user.company_id:
            raise PermissionDeniedException("You do not have permission to view this retirement")

    return APIResponse(
        success=True,
        message="Retirement details retrieved successfully",
        data={
            "id": str(ret.id),
            "ownership_id": str(ret.ownership_id),
            "company_id": str(ret.company_id),
            "company_name": ret.company.name if ret.company else None,
            "credits_retired": float(ret.credits_retired),
            "reason": ret.reason,
            "certificate_number": ret.certificate_number,
            "blockchain_tx_hash": ret.blockchain_tx_hash,
            "retired_at": ret.retired_at.isoformat()
        }
    )


@router.get("/{retirement_id}/certificate", response_model=APIResponse[dict])
def get_retirement_certificate(
    retirement_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    service: RetirementService = Depends(get_retirement_service)
):
    """
    Retrieves dynamic retirement certificate metadata.
    """
    ret = service.get_retirement(retirement_id)
    if current_user.role not in [UserRole.ADMIN, UserRole.AUDITOR]:
        if ret.company_id != current_user.company_id:
            raise PermissionDeniedException("You do not have permission to view this certificate")

    cert_data = service.generate_certificate(retirement_id)
    return APIResponse(
        success=True,
        message="Retirement certificate retrieved successfully",
        data=cert_data
    )
