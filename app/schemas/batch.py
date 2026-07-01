from datetime import date, datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.models import BatchStatus


class CreditBatchBase(BaseModel):
    project_id: uuid.UUID
    batch_number: str = Field(..., min_length=2, max_length=100, examples=["BATCH-2024-001"])
    vintage_year: int = Field(..., ge=2000, le=datetime.now().year + 5, examples=[2024])
    total_credits: float = Field(..., gt=0.0, examples=[50000.0000])
    remaining_credits: float = Field(..., ge=0.0, examples=[50000.0000])
    issuance_date: date = Field(..., examples=["2024-06-15"])
    metadata_json: Optional[Dict[str, Any]] = Field(None, examples=[{"methodology_version": "1.2"}])


class CreditBatchCreate(CreditBatchBase):
    company_id: Optional[uuid.UUID] = Field(None, examples=["d3b07384-d113-4ec5-a55e-04d800000000"])

    @field_validator("vintage_year")
    @classmethod
    def validate_vintage_year(cls, v: int) -> int:
        current_year = datetime.now().year
        if v > current_year:
            raise ValueError(f"Vintage year cannot exceed current year ({current_year})")
        return v

    @field_validator("remaining_credits")
    @classmethod
    def validate_credits(cls, v: float, info) -> float:
        total_credits = info.data.get("total_credits")
        if total_credits is not None and v > total_credits:
            raise ValueError("Remaining credits cannot exceed total credits")
        return v


class CreditBatchUpdate(BaseModel):
    batch_number: Optional[str] = Field(None, min_length=2, max_length=100)
    vintage_year: Optional[int] = Field(None, ge=2000)
    total_credits: Optional[float] = Field(None, gt=0.0)
    remaining_credits: Optional[float] = Field(None, ge=0.0)
    issuance_date: Optional[date] = Field(None)
    status: Optional[BatchStatus] = Field(None)
    metadata_json: Optional[Dict[str, Any]] = Field(None)

    @field_validator("vintage_year")
    @classmethod
    def validate_vintage_year(cls, v: Optional[int]) -> Optional[int]:
        if v is not None:
            current_year = datetime.now().year
            if v > current_year:
                raise ValueError(f"Vintage year cannot exceed current year ({current_year})")
        return v

    @field_validator("remaining_credits")
    @classmethod
    def validate_credits(cls, v: Optional[float], info) -> Optional[float]:
        total_credits = info.data.get("total_credits")
        if total_credits is not None and v is not None and v > total_credits:
            raise ValueError("Remaining credits cannot exceed total credits")
        return v


class CreditBatchResponse(CreditBatchBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: BatchStatus
    created_at: datetime
    updated_at: datetime


class CreditBatchListResponse(BaseModel):
    batches: List[CreditBatchResponse]
