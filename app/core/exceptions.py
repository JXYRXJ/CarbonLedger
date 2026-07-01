import logging
from typing import Any, Dict, List, Union
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class APIException(Exception):
    """
    Base exception class for all custom CarbonLedger API errors.
    """
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        errors: Union[List[Any], None] = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.errors = errors or []


class ValidationException(APIException):
    """
    Exception raised when input validation fails.
    """
    def __init__(self, message: str = "Input validation failed", errors: Union[List[Any], None] = None) -> None:
        super().__init__(message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, errors=errors)


class AuthenticationException(APIException):
    """
    Exception raised when authentication fails or is missing.
    """
    def __init__(self, message: str = "Authentication failed", errors: Union[List[Any], None] = None) -> None:
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED, errors=errors)


class AuthorizationException(APIException):
    """
    Exception raised when permission is denied for a resource.
    """
    def __init__(self, message: str = "Not authorized to access this resource", errors: Union[List[Any], None] = None) -> None:
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN, errors=errors)


class NotFoundException(APIException):
    """
    Exception raised when a requested resource is not found.
    """
    def __init__(self, message: str = "Resource not found", errors: Union[List[Any], None] = None) -> None:
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND, errors=errors)


class ConflictException(APIException):
    """
    Exception raised when resource state conflicts (e.g. duplicate key).
    """
    def __init__(self, message: str = "Resource state conflict", errors: Union[List[Any], None] = None) -> None:
        super().__init__(message, status_code=status.HTTP_409_CONFLICT, errors=errors)


class DatabaseException(APIException):
    """
    Exception raised when database transactions fail.
    """
    def __init__(self, message: str = "Database operation failed", errors: Union[List[Any], None] = None) -> None:
        super().__init__(message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, errors=errors)


class BlockchainException(APIException):
    """
    Exception raised when blockchain verification or audits fail.
    """
    def __init__(self, message: str = "Blockchain audit log or verification failed", errors: Union[List[Any], None] = None) -> None:
        super().__init__(message, status_code=status.HTTP_502_BAD_GATEWAY, errors=errors)


class InvalidCredentialsException(AuthenticationException):
    def __init__(self, message: str = "Invalid email or password", errors: Union[List[Any], None] = None) -> None:
        super().__init__(message, errors=errors)


class ExpiredTokenException(AuthenticationException):
    def __init__(self, message: str = "Token has expired", errors: Union[List[Any], None] = None) -> None:
        super().__init__(message, errors=errors)


class InvalidTokenException(AuthenticationException):
    def __init__(self, message: str = "Invalid token structure", errors: Union[List[Any], None] = None) -> None:
        super().__init__(message, errors=errors)


class PermissionDeniedException(AuthorizationException):
    def __init__(self, message: str = "Permission denied to perform this action", errors: Union[List[Any], None] = None) -> None:
        super().__init__(message, errors=errors)


class UserInactiveException(AuthorizationException):
    def __init__(self, message: str = "User account is currently deactivated", errors: Union[List[Any], None] = None) -> None:
        super().__init__(message, errors=errors)


class CompanyInactiveException(AuthorizationException):
    def __init__(self, message: str = "Company status is not active", errors: Union[List[Any], None] = None) -> None:
        super().__init__(message, errors=errors)


class DuplicateResourceException(ConflictException):
    def __init__(self, message: str = "Resource already exists", errors: Union[List[Any], None] = None) -> None:
        super().__init__(message, errors=errors)


class BusinessRuleException(APIException):
    def __init__(self, message: str = "Business rule constraint violated", errors: Union[List[Any], None] = None) -> None:
        super().__init__(message, status_code=status.HTTP_400_BAD_REQUEST, errors=errors)


def register_exception_handlers(app: FastAPI) -> None:
    """
    Registers custom, validation, and global fallback exception handlers on the FastAPI app.
    """

    @app.exception_handler(APIException)
    async def custom_api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
        """
        Handler for all custom APIException subclasses.
        """
        # Log error details (warnings for client errors, errors for server-side issues)
        log_level = logging.WARNING if exc.status_code < 500 else logging.ERROR
        logger.log(log_level, f"API Exception: {exc.message} (status: {exc.status_code}) - errors: {exc.errors}")

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.message,
                "errors": exc.errors
            }
        )

    @app.exception_handler(RequestValidationError)
    async def pydantic_validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """
        Handler for Pydantic input validation failures.
        """
        formatted_errors = []
        for error in exc.errors():
            loc = ".".join(str(x) for x in error.get("loc", []))
            # Remove body prefix if present for cleaner user messages
            if loc.startswith("body."):
                loc = loc[5:]
            formatted_errors.append({
                "field": loc,
                "message": error.get("msg", "Invalid value"),
                "type": error.get("type", "value_error")
            })

        logger.warning(f"Request validation failure on {request.method} {request.url.path}: {formatted_errors}")

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "message": "Validation failed",
                "errors": formatted_errors
            }
        )

    @app.exception_handler(ValidationError)
    async def pydantic_internal_validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
        """
        Handler for internal Pydantic ValidationError (e.g. output validation failure).
        """
        formatted_errors = []
        for error in exc.errors():
            loc = ".".join(str(x) for x in error.get("loc", []))
            formatted_errors.append({
                "field": loc,
                "message": error.get("msg", "Invalid output shape"),
                "type": error.get("type", "value_error")
            })

        logger.error(f"Internal structure validation failure: {formatted_errors}")

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "Internal response validation error",
                "errors": formatted_errors if not app.debug else []
            }
        )

    @app.exception_handler(Exception)
    async def global_fallback_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        Catches and logs all unhandled exceptions, returning a clean 500 error structure.
        """
        logger.exception(f"Unhandled exception caught on {request.method} {request.url.path}: {str(exc)}")

        # Retrieve debug state from app
        debug = getattr(app, "debug", False)
        error_details = [str(exc)] if debug else []

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "An unexpected error occurred on the server",
                "errors": error_details
            }
        )
