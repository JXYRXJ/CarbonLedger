import math
from typing import Any, List, TypeVar
from app.schemas.pagination import PaginatedResponse, PaginationMetadata

T = TypeVar("T")


def paginate_list(items: List[T], total_count: int, page: int, limit: int) -> PaginatedResponse[T]:
    """
    Constructs a standard PaginatedResponse wrapper around a slice of items.
    """
    total_pages = math.ceil(total_count / limit) if limit > 0 else 0

    metadata = PaginationMetadata(
        total=total_count,
        page=page,
        limit=limit,
        pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )

    return PaginatedResponse(
        items=items,
        pagination=metadata
    )
