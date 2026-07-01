from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.models import UserRole


class UserBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100, examples=["John"])
    last_name: str = Field(..., min_length=1, max_length=100, examples=["Doe"])
    email: EmailStr = Field(..., examples=["john.doe@example.com"])
    role: UserRole = Field(default=UserRole.VIEWER, examples=["TRADER"])


class UserCreate(UserBase):
    company_id: Optional[uuid.UUID] = Field(None, description="The ID of the company this user belongs to")
    password: str = Field(..., min_length=8, max_length=100, description="Plain text password, min 8 chars")


class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = Field(None)
    role: Optional[UserRole] = Field(None)
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    is_active: Optional[bool] = Field(None)


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: Optional[uuid.UUID] = None
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class UserListResponse(BaseModel):
    users: List[UserResponse]
