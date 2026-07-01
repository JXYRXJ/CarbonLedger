from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator
import re


class RetirementBase(BaseModel):
    ownership_id: uuid.UUID
    company_id: uuid.UUID
    credits_retired: float = Field(..., gt=0.0, examples=[500.0000])
    reason: str = Field(..., min_length=5, examples=["Offsetting Q2 2026 Scope 1 Emissions"])
    certificate_number: str = Field(..., min_length=2, max_length=100, examples=["CERT-998877"])
    blockchain_tx_hash: Optional[str] = Field(None, examples=["0x39a1b181db8fa0b08def02a80be3e9e14a1e9e2b0a1d64380eb9a399dc0e2101"])


class RetirementCreate(RetirementBase):
    @field_validator("blockchain_tx_hash")
    @classmethod
    def validate_tx_hash(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not re.match(r"^0x[a-fA-F0-9]{64}$", v):
                raise ValueError("Blockchain transaction hash must be a valid 64-character hex string prefixed with 0x")
        return v


class RetirementUpdate(BaseModel):
    # Status updates for retirement records are usually minimal, but certificate and tx can complete asynchronously
    certificate_number: Optional[str] = Field(None, min_length=2, max_length=100)
    blockchain_tx_hash: Optional[str] = Field(None)
    retired_at: Optional[datetime] = Field(None)

    @field_validator("blockchain_tx_hash")
    @classmethod
    def validate_tx_hash(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not re.match(r"^0x[a-fA-F0-9]{64}$", v):
                raise ValueError("Blockchain transaction hash must be a valid 64-character hex string prefixed with 0x")
        return v


class RetirementResponse(RetirementBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    retired_at: datetime
    created_at: datetime
    updated_at: datetime


class RetirementListResponse(BaseModel):
    retirements: List[RetirementResponse]
