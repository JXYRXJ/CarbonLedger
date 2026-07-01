from datetime import date, datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.models import DocumentType


# ==============================================================================
# PROJECT DOCUMENT SCHEMAS
# ==============================================================================

class ProjectDocumentBase(BaseModel):
    document_type: DocumentType = Field(..., examples=[DocumentType.VERIFICATION_CERTIFICATE])
    file_name: str = Field(..., min_length=1, max_length=255, examples=["certificate.pdf"])
    file_url: str = Field(..., max_length=1024, examples=["https://storage.carbonledger.com/docs/certificate.pdf"])


class ProjectDocumentCreate(ProjectDocumentBase):
    project_id: uuid.UUID


class ProjectDocumentResponse(ProjectDocumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    uploaded_at: datetime
    created_at: datetime
    updated_at: datetime


# ==============================================================================
# CARBON PROJECT SCHEMAS
# ==============================================================================

class CarbonProjectBase(BaseModel):
    registry_id: uuid.UUID
    project_code: str = Field(..., min_length=2, max_length=100, examples=["VCS-983"])
    name: str = Field(..., min_length=2, max_length=255, examples=["Amazon Reforestation Project"])
    country: str = Field(..., min_length=2, max_length=100, examples=["Brazil"])
    project_type: str = Field(..., min_length=2, max_length=100, examples=["Forestry"])
    verification_standard: str = Field(..., min_length=2, max_length=100, examples=["VCS"])
    methodology: str = Field(..., min_length=2, max_length=255, examples=["VM0007"])
    description: Optional[str] = Field(None, examples=["This project preserves carbon stocks in the Amazon."])
    developer: str = Field(..., min_length=2, max_length=255, examples=["Greenhouse Assets LLC"])
    start_date: date = Field(..., examples=["2020-01-01"])
    end_date: date = Field(..., examples=["2030-12-31"])


class CarbonProjectCreate(CarbonProjectBase):
    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, v: date, info) -> date:
        start_date = info.data.get("start_date")
        if start_date and v < start_date:
            raise ValueError("end_date must be equal to or after start_date")
        return v


class CarbonProjectUpdate(BaseModel):
    registry_id: Optional[uuid.UUID] = Field(None)
    project_code: Optional[str] = Field(None, min_length=2, max_length=100)
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    country: Optional[str] = Field(None, min_length=2, max_length=100)
    project_type: Optional[str] = Field(None, min_length=2, max_length=100)
    verification_standard: Optional[str] = Field(None, min_length=2, max_length=100)
    methodology: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = Field(None)
    developer: Optional[str] = Field(None, min_length=2, max_length=255)
    start_date: Optional[date] = Field(None)
    end_date: Optional[date] = Field(None)
    status: Optional[str] = Field(None, max_length=50)

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, v: Optional[date], info) -> Optional[date]:
        start_date = info.data.get("start_date")
        if start_date and v and v < start_date:
            raise ValueError("end_date must be equal to or after start_date")
        return v


class CarbonProjectResponse(CarbonProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    documents: List[ProjectDocumentResponse] = []


class CarbonProjectListResponse(BaseModel):
    projects: List[CarbonProjectResponse]
