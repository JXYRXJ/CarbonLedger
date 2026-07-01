from typing import Any, Optional
from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.dependencies import get_auth_service, get_current_active_user, get_db
from app.models.models import User, Company
from app.schemas.responses import APIResponse
from app.schemas.user import UserResponse
from app.schemas.company import CompanyResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ==============================================================================
# INPUT SCHEMA SCHEMAS
# ==============================================================================

class RegisterRequest(BaseModel):
    first_name: str = Field(..., examples=["John"])
    last_name: str = Field(..., examples=["Doe"])
    email: EmailStr = Field(..., examples=["admin@acme.com"])
    password: str = Field(..., min_length=8, description="Strong password matching rules", examples=["P@ssw0rd123!"])
    company_name: str = Field(..., examples=["Acme Corporation"])
    registration_number: str = Field(..., examples=["CO-9876543-X"])
    country: str = Field(..., examples=["United States"])
    industry: Optional[str] = Field(None, examples=["Technology"])
    website: Optional[str] = Field(None, examples=["https://acme.com"])
    wallet_address: Optional[str] = Field(None, examples=["0x71C7656EC7ab88b098defB751B7401B5f6d8976F"])


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., examples=["admin@acme.com"])
    password: str = Field(..., examples=["P@ssw0rd123!"])


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."])


# ==============================================================================
# ROUTE ENDPOINTS
# ==============================================================================

@router.post("/register", response_model=APIResponse[dict], status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    auth_service: Any = Depends(get_auth_service)
) -> APIResponse[dict]:
    """
    Registers a new company and registers its initial Company Admin user.
    Generates and returns JWT token credentials.
    """
    user, company, access_token, refresh_token = auth_service.register_company_and_admin(payload.model_dump())
    
    data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user),
        "company": CompanyResponse.model_validate(company)
    }
    return APIResponse(
        message="Registration successful. Company and Admin created.",
        data=data
    )


@router.post("/login", response_model=APIResponse[dict])
def login(
    payload: LoginRequest,
    request: Request,
    auth_service: Any = Depends(get_auth_service)
) -> APIResponse[dict]:
    """
    Authenticates a user's email and password.
    Returns access/refresh token pair and user profile details.
    """
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")
    
    user, company, access_token, refresh_token = auth_service.login_user(payload.model_dump(), ip, ua)
    
    data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user),
        "company": CompanyResponse.model_validate(company) if company else None
    }
    return APIResponse(
        message="Login successful",
        data=data
    )


@router.post("/refresh", response_model=APIResponse[dict])
def refresh(
    payload: RefreshRequest,
    request: Request,
    auth_service: Any = Depends(get_auth_service)
) -> APIResponse[dict]:
    """
    Refreshes the caller's session. Implements Refresh Token Rotation (RTR).
    """
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")
    
    access_token, refresh_token = auth_service.refresh_access_tokens(payload.refresh_token, ip, ua)
    
    data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }
    return APIResponse(
        message="Token refreshed successfully",
        data=data
    )


@router.post("/logout", response_model=APIResponse[dict])
def logout(
    payload: RefreshRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    auth_service: Any = Depends(get_auth_service)
) -> APIResponse[dict]:
    """
    Terminates the user's active session by revoking the refresh token.
    """
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")
    
    auth_service.logout_user(payload.refresh_token, current_user.id, ip, ua)
    
    return APIResponse(
        message="Logout successful",
        data={}
    )


@router.get("/me", response_model=APIResponse[dict])
def get_me(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> APIResponse[dict]:
    """
    Returns the caller's active user profile details, roles, and company association.
    """
    company = None
    if current_user.company_id:
        company = db.query(Company).filter(Company.id == current_user.company_id).first()
        
    data = {
        "user": UserResponse.model_validate(current_user),
        "company": CompanyResponse.model_validate(company) if company else None,
        "role": current_user.role.value
    }
    return APIResponse(
        message="Profile details retrieved",
        data=data
    )


# Need to define typing Any for get_auth_service resolution in local scopes
from typing import Any
