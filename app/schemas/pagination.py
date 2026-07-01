from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """
    Query parameters for fetching paginated lists.
    """
    page: int = Field(default=1, ge=1, description="Page number, starting at 1")
    limit: int = Field(default=10, ge=1, le=100, description="Number of items per page")
    sort: Optional[str] = Field(default=None, description="Field name to sort by")
    order: str = Field(default="asc", description="Sorting direction: 'asc' or 'desc'")
    search: Optional[str] = Field(default=None, description="Search query string")


class PaginationMetadata(BaseModel):
    """
    Metadata summarizing the pagination state of the returned results.
    """
    total: int = Field(..., description="Total count of items matching the query")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Page size limit")
    pages: int = Field(..., description="Total pages available based on count and limit")
    has_next: bool = Field(..., description="Flag indicating if there is a next page")
    has_prev: bool = Field(..., description="Flag indicating if there is a previous page")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic container for returning paginated records with metadata.
    """
    items: List[T] = Field(..., description="List of items on the current page")
    pagination: PaginationMetadata
