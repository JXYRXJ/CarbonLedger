from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, EmailStr, Field

from app.core.dependencies import get_current_active_user, get_service
from app.models.models import User
from app.schemas.responses import APIResponse
from app.schemas.user import UserResponse
from app.repositories.repositories import UserRepository
from app.services.services import UserService

router = APIRouter(prefix="/users", tags=["Users"])


# ==============================================================================
# INPUT SCHEMAS
# ==============================================================================

class UpdateProfileRequest(BaseModel):
    first_name: str = Field(..., examples=["John"])
    last_name: str = Field(..., examples=["Doe"])
    email: EmailStr = Field(..., examples=["john.doe@example.com"])


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="Strong password matching rules")


# ==============================================================================
# ROUTE ENDPOINTS
# ==============================================================================

@router.get("/me", response_model=APIResponse[UserResponse])
def get_me(current_user: User = Depends(get_current_active_user)) -> APIResponse[UserResponse]:
    """
    Returns the caller's active user profile details.
    """
    return APIResponse(
        message="User profile details retrieved",
        data=UserResponse.model_validate(current_user)
    )


@router.patch("/profile", response_model=APIResponse[UserResponse])
def update_profile(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_service(UserService, UserRepository))
) -> APIResponse[UserResponse]:
    """
    Updates the caller's profile attributes (first name, last name, and email).
    """
    updated_user = user_service.update_profile(
        current_user.id,
        payload.first_name,
        payload.last_name,
        payload.email
    )
    return APIResponse(
        message="Profile details updated successfully",
        data=UserResponse.model_validate(updated_user)
    )


@router.patch("/change-password", response_model=APIResponse[dict])
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_service(UserService, UserRepository))
) -> APIResponse[dict]:
    """
    Updates the caller's security credentials after verifying their current password.
    """
    user_service.change_password(current_user.id, payload.old_password, payload.new_password)
    return APIResponse(
        message="Password updated successfully",
        data={}
    )


@router.patch("/deactivate", response_model=APIResponse[dict])
def deactivate_self(
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_service(UserService, UserRepository))
) -> APIResponse[dict]:
    """
    Self-deactivates the user's account session.
    """
    user_service.deactivate_user(current_user.id)
    return APIResponse(
        message="User account successfully deactivated",
        data={}
    )
