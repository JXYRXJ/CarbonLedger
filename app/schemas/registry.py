from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class RegistryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, examples=["Verra Verified Carbon Standard"])
    country: str = Field(..., min_length=2, max_length=100, examples=["United States"])
    website: str = Field(..., max_length=255, examples=["https://verra.org"])
    accreditation: str = Field(..., max_length=255, examples=["ANSI Accredited"])
    description: Optional[str] = Field(None, examples=["Verra manages the VCS standard."])


class RegistryCreate(RegistryBase):
    pass


class RegistryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    country: Optional[str] = Field(None, min_length=2, max_length=100)
    website: Optional[str] = Field(None, max_length=255)
    accreditation: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None)
    status: Optional[str] = Field(None, max_length=50)


class RegistryResponse(RegistryBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class RegistryListResponse(BaseModel):
    registries: List[RegistryResponse]
