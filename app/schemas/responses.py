from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """
    Standard successful response wrapper.
    """
    success: bool = Field(default=True, description="Indicates if the operation succeeded")
    message: str = Field(default="Success", description="User-friendly status message")
    data: T = Field(..., description="Payload data returned by the operation")


class ErrorDetails(BaseModel):
    """
    Detailed validation or operation error structure.
    """
    field: Optional[str] = Field(default=None, description="The request field that caused the error (if validation)")
    message: str = Field(..., description="Specific explanation of this failure")
    type: Optional[str] = Field(default=None, description="Categorization or system code for this error type")


class ErrorResponse(BaseModel):
    """
    Standard error response wrapper returned for non-2xx status codes.
    """
    success: bool = Field(default=False, description="Indicates if the operation failed")
    message: str = Field(..., description="General explanation of what went wrong")
    errors: List[Any] = Field(default_factory=list, description="Array of detailed error items (such as field validations)")
