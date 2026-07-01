from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator
import re


class TransactionBase(BaseModel):
    order_id: uuid.UUID
    buyer_company_id: uuid.UUID
    seller_company_id: uuid.UUID
    ownership_id: uuid.UUID
    credits_transferred: float = Field(..., gt=0.0, examples=[500.0000])
    price_per_credit: float = Field(..., gt=0.0, examples=[15.50])
    total_price: float = Field(..., gt=0.0, examples=[7750.00])
    blockchain_tx_hash: Optional[str] = Field(None, examples=["0x71190cf611be24cfabcf153dfc27e02df3b924741400e47087f98d7990c74d6c"])
    status: str = Field(default="PENDING", examples=["confirmed"])

    @field_validator("blockchain_tx_hash")
    @classmethod
    def validate_tx_hash(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not re.match(r"^0x[a-fA-F0-9]{64}$", v):
                raise ValueError("Blockchain transaction hash must be a valid 64-character hex string prefixed with 0x")
        return v


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    blockchain_tx_hash: Optional[str] = Field(None)
    status: Optional[str] = Field(None, max_length=50)
    completed_at: Optional[datetime] = Field(None)

    @field_validator("blockchain_tx_hash")
    @classmethod
    def validate_tx_hash(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not re.match(r"^0x[a-fA-F0-9]{64}$", v):
                raise ValueError("Blockchain transaction hash must be a valid 64-character hex string prefixed with 0x")
        return v


class TransactionResponse(TransactionBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class TransactionListResponse(BaseModel):
    transactions: List[TransactionResponse]
