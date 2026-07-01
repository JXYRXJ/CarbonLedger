from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class OwnershipBase(BaseModel):
    batch_id: uuid.UUID
    company_id: uuid.UUID
    owned_credits: float = Field(..., gt=0.0, examples=[15000.0000])
    average_purchase_price: float = Field(..., ge=0.0, examples=[14.50])


class OwnershipCreate(OwnershipBase):
    pass


class OwnershipUpdate(BaseModel):
    owned_credits: Optional[float] = Field(None, gt=0.0)
    average_purchase_price: Optional[float] = Field(None, ge=0.0)


class OwnershipResponse(OwnershipBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class OwnershipListResponse(BaseModel):
    ownerships: List[OwnershipResponse]
