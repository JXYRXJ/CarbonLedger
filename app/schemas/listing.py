from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field

from app.models.models import ListingStatus


class MarketplaceListingBase(BaseModel):
    ownership_id: uuid.UUID
    seller_company_id: uuid.UUID
    credits_for_sale: float = Field(..., gt=0.0, examples=[1000.0000])
    price_per_credit: float = Field(..., gt=0.0, examples=[15.50])
    minimum_purchase: float = Field(default=1.0, ge=1.0, examples=[10.0])
    description: Optional[str] = Field(None, examples=["VCS reforestation credits for sale."])
    expires_at: Optional[datetime] = Field(None, examples=["2026-12-31T23:59:59Z"])


class MarketplaceListingCreate(MarketplaceListingBase):
    pass


class MarketplaceListingUpdate(BaseModel):
    credits_for_sale: Optional[float] = Field(None, gt=0.0)
    price_per_credit: Optional[float] = Field(None, gt=0.0)
    minimum_purchase: Optional[float] = Field(None, ge=1.0)
    description: Optional[str] = Field(None)
    status: Optional[ListingStatus] = Field(None)
    expires_at: Optional[datetime] = Field(None)


class MarketplaceListingResponse(MarketplaceListingBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: ListingStatus
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class MarketplaceListingListResponse(BaseModel):
    listings: List[MarketplaceListingResponse]
