from typing import List, Optional
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from app.core.dependencies import get_current_company, get_service, RequireRole
from app.models.models import Company, User, UserRole
from app.schemas.responses import APIResponse
from app.schemas.company import CompanyResponse
from app.schemas.user import UserResponse
from app.repositories.repositories import CompanyRepository
from app.services.services import CompanyService

router = APIRouter(prefix="/companies", tags=["Companies"])


# ==============================================================================
# INPUT SCHEMAS
# ==============================================================================

class UpdateCompanyRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255, examples=["Acme Solutions Inc"])
    industry: Optional[str] = Field(None, max_length=100, examples=["Clean Tech"])
    country: Optional[str] = Field(None, min_length=2, max_length=100, examples=["United States"])
    website: Optional[str] = Field(None, max_length=255, examples=["https://acme-solutions.com"])
    email_domain: Optional[str] = Field(None, max_length=100, examples=["acme-solutions.com"])


class UpdateWalletRequest(BaseModel):
    wallet_address: str = Field(..., description="Valid Ethereum Hex Wallet Address", examples=["0x71C7656EC7ab88b098defB751B7401B5f6d8976F"])


# ==============================================================================
# ROUTE ENDPOINTS
# ==============================================================================

@router.get("/me", response_model=APIResponse[CompanyResponse])
def get_me(
    company: Company = Depends(get_current_company),
    admin_check: User = Depends(RequireRole([UserRole.COMPANY_ADMIN]))
) -> APIResponse[CompanyResponse]:
    """
    Returns the caller's enterprise company profile. Restricted to Company Admin.
    """
    return APIResponse(
        message="Company profile retrieved successfully",
        data=CompanyResponse.model_validate(company)
    )


@router.patch("", response_model=APIResponse[CompanyResponse])
def update_company(
    payload: UpdateCompanyRequest,
    company: Company = Depends(get_current_company),
    admin_check: User = Depends(RequireRole([UserRole.COMPANY_ADMIN])),
    company_service: CompanyService = Depends(get_service(CompanyService, CompanyRepository))
) -> APIResponse[CompanyResponse]:
    """
    Updates general metadata attributes of the company. Restricted to Company Admin.
    """
    updated = company_service.update_company(company.id, payload.model_dump(exclude_unset=True))
    return APIResponse(
        message="Company profile updated successfully",
        data=CompanyResponse.model_validate(updated)
    )


@router.patch("/wallet", response_model=APIResponse[CompanyResponse])
def update_wallet(
    payload: UpdateWalletRequest,
    company: Company = Depends(get_current_company),
    admin_check: User = Depends(RequireRole([UserRole.COMPANY_ADMIN])),
    company_service: CompanyService = Depends(get_service(CompanyService, CompanyRepository))
) -> APIResponse[CompanyResponse]:
    """
    Sets or updates the company's registry wallet address. Restricted to Company Admin.
    """
    updated = company_service.update_wallet(company.id, payload.wallet_address)
    return APIResponse(
        message="Company wallet address updated successfully",
        data=CompanyResponse.model_validate(updated)
    )


@router.get("/users", response_model=APIResponse[List[UserResponse]])
def list_company_users(
    company: Company = Depends(get_current_company),
    admin_check: User = Depends(RequireRole([UserRole.COMPANY_ADMIN])),
    company_service: CompanyService = Depends(get_service(CompanyService, CompanyRepository))
) -> APIResponse[List[UserResponse]]:
    """
    Lists all platform users registered under the caller's enterprise company context. Restricted to Company Admin.
    """
    users = company_service.list_users(company.id)
    serialized_users = [UserResponse.model_validate(u) for u in users]
    
    return APIResponse(
        message="Company users list retrieved successfully",
        data=serialized_users
    )
