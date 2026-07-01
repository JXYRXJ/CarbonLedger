from typing import List, Optional
import uuid
from pydantic import BaseModel, Field


class CompanySummary(BaseModel):
    id: uuid.UUID
    name: str
    registration_number: str
    wallet_address: Optional[str] = None


class PortfolioSummary(BaseModel):
    owned_credit_count: float = Field(..., description="Total credits currently owned")
    available_credit_count: float = Field(..., description="Credits available for sale or retirement")
    listed_credit_count: float = Field(..., description="Credits locked in active marketplace listings")
    retired_credit_count: float = Field(..., description="Total credits retired by the company")
    estimated_portfolio_value: float = Field(..., description="Total book value of the portfolio")


class OwnedBatchProject(BaseModel):
    id: uuid.UUID
    name: str
    project_code: str
    country: str


class OwnedBatchRegistry(BaseModel):
    id: uuid.UUID
    name: str


class OwnedBatchItem(BaseModel):
    ownership_id: uuid.UUID
    batch_id: uuid.UUID
    batch_number: str
    vintage_year: int
    status: str
    total_credits_owned: float
    available_credits: float
    listed_credits: float
    average_purchase_price: Optional[float] = None
    project: Optional[OwnedBatchProject] = None
    registry: Optional[OwnedBatchRegistry] = None


class PortfolioResponse(BaseModel):
    company: CompanySummary
    portfolio_summary: PortfolioSummary
    owned_batches: List[OwnedBatchItem]
