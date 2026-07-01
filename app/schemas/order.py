from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.models import PurchaseOrderStatus


class PurchaseOrderBase(BaseModel):
    listing_id: uuid.UUID
    buyer_company_id: uuid.UUID
    requested_credits: float = Field(..., gt=0.0, examples=[500.0000])
    price_per_credit: float = Field(..., gt=0.0, examples=[15.50])
    total_price: float = Field(..., gt=0.0, examples=[7750.00])
    payment_reference: Optional[str] = Field(None, max_length=255, examples=["PAY-REF-998877"])


class PurchaseOrderCreate(PurchaseOrderBase):
    @field_validator("total_price")
    @classmethod
    def validate_total_price(cls, v: float, info) -> float:
        req = info.data.get("requested_credits")
        price = info.data.get("price_per_credit")
        if req is not None and price is not None:
            expected = round(req * price, 2)
            # Allow minor rounding differences if price is a float
            if abs(v - expected) > 0.05:
                raise ValueError(f"total_price ({v}) must match expected calculation: requested_credits * price_per_credit ({expected})")
        return v


class PurchaseOrderUpdate(BaseModel):
    status: Optional[PurchaseOrderStatus] = Field(None)
    payment_reference: Optional[str] = Field(None, max_length=255)


class PurchaseOrderResponse(PurchaseOrderBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: PurchaseOrderStatus
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class PurchaseOrderListResponse(BaseModel):
    orders: List[PurchaseOrderResponse]
