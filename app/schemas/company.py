from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator
import re

from app.models.models import CompanyStatus


class CompanyBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, examples=["Acme Carbon Corp"])
    registration_number: str = Field(..., min_length=3, max_length=100, examples=["CO-9876543-X"])
    industry: Optional[str] = Field(None, max_length=100, examples=["Technology"])
    country: str = Field(..., min_length=2, max_length=100, examples=["United States"])
    website: Optional[str] = Field(None, max_length=255, examples=["https://acme.com"])
    wallet_address: Optional[str] = Field(None, examples=["0x71C7656EC7ab88b098defB751B7401B5f6d8976F"])
    email_domain: Optional[str] = Field(None, max_length=100, examples=["acme.com"])

    @field_validator("wallet_address")
    @classmethod
    def validate_ethereum_address(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not re.match(r"^0x[a-fA-F0-9]{40}$", v):
                raise ValueError("Wallet address must be a valid Ethereum hexadecimal address starting with 0x")
        return v


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    registration_number: Optional[str] = Field(None, min_length=3, max_length=100)
    industry: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, min_length=2, max_length=100)
    website: Optional[str] = Field(None, max_length=255)
    wallet_address: Optional[str] = Field(None)
    email_domain: Optional[str] = Field(None, max_length=100)
    status: Optional[CompanyStatus] = Field(None)

    @field_validator("wallet_address")
    @classmethod
    def validate_ethereum_address(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not re.match(r"^0x[a-fA-F0-9]{40}$", v):
                raise ValueError("Wallet address must be a valid Ethereum hexadecimal address starting with 0x")
        return v


class CompanyResponse(CompanyBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: CompanyStatus
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class CompanyListResponse(BaseModel):
    companies: List[CompanyResponse]
