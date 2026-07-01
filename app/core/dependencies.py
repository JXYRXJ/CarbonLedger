from typing import Any, Generator, List, Optional, Type
import uuid
from fastapi import Depends, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import (
    AuthenticationException,
    AuthorizationException,
    PermissionDeniedException,
    UserInactiveException,
    CompanyInactiveException
)
from app.core.security import decode_token
from app.models.models import Company, User, UserRole, CompanyStatus
from app.schemas.pagination import PaginationParams

# Define oauth2 scheme
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False
)


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Decodes the JWT token and fetches the User from the database.
    """
    if not token:
        raise AuthenticationException("Authentication credentials are required. Please log in.")

    # decode_token handles ExpiredTokenException and InvalidTokenException
    payload = decode_token(token)
    user_id_str = payload.get("sub")
    token_type = payload.get("type")

    if not user_id_str or token_type != "access":
        raise AuthenticationException("Invalid token format or incorrect token type")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError as exc:
        raise AuthenticationException("Invalid user ID representation in access token") from exc

    user = db.query(User).filter(User.id == user_id, User.deleted_at == None).first()
    if not user:
        raise AuthenticationException("The user account associated with this token does not exist.")

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Ensures that the user account is active.
    """
    if not current_user.is_active:
        raise UserInactiveException("User account is inactive. Please contact support.")
    return current_user


def get_current_company(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Company:
    """
    Retrieves the caller's active company.
    """
    if not current_user.company_id:
        raise CompanyInactiveException("User profile is not associated with an enterprise company profile.")

    company = db.query(Company).filter(Company.id == current_user.company_id, Company.deleted_at == None).first()
    if not company or company.status != CompanyStatus.ACTIVE:
        raise CompanyInactiveException("Associated company profile is suspended or deactivated.")

    return company


def get_current_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Guarantees that the calling user holds the system Administrator role.
    """
    if current_user.role != UserRole.ADMIN:
        raise PermissionDeniedException("System Administrator role is required to perform this action.")
    return current_user


class RequireRole:
    """
    Dependency checking that the user role belongs to a defined whitelist.
    Usage: current_user: User = Depends(RequireRole([UserRole.COMPANY_ADMIN]))
    """
    def __init__(self, allowed_roles: List[UserRole]) -> None:
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in self.allowed_roles:
            role_names = [role.value for role in self.allowed_roles]
            raise PermissionDeniedException(f"Permission denied. Required roles: {', '.join(role_names)}")
        return current_user


def get_pagination_params(
    page: int = Query(default=1, ge=1, description="Page number, starting at 1"),
    limit: int = Query(default=10, ge=1, le=100, description="Items per page limit"),
    sort: Optional[str] = Query(default=None, description="Field name to sort by"),
    order: str = Query(default="asc", description="Sorting direction: 'asc' or 'desc'"),
    search: Optional[str] = Query(default=None, description="Search query string")
) -> PaginationParams:
    """
    Validates and packs pagination and sorting inputs into a PaginationParams instance.
    """
    order = order.lower() if order else "asc"
    if order not in ["asc", "desc"]:
        order = "asc"

    return PaginationParams(
        page=page,
        limit=limit,
        sort=sort,
        order=order,
        search=search
    )


def get_repository(repo_class: Type[Any]) -> Any:
    """
    FastAPI dependency factory to inject a repository instance pre-bound to the DB session.
    Example: Depends(get_repository(UserRepository))
    """
    def _inject_repository(db: Session = Depends(get_db)) -> Any:
        return repo_class(db=db)
    return _inject_repository


def get_service(service_class: Type[Any], repo_class: Optional[Type[Any]] = None) -> Any:
    """
    FastAPI dependency factory to inject a service instance, automatically constructing
    the service's dependent repository if specified.
    Example: Depends(get_service(UserService, UserRepository))
    """
    def _inject_service(
        db: Session = Depends(get_db),
        repo: Optional[Any] = Depends(get_repository(repo_class)) if repo_class else None
    ) -> Any:
        if repo:
            return service_class(repository=repo)
        return service_class(db=db)
    return _inject_service


def get_auth_service(db: Session = Depends(get_db)) -> Any:
    """
    Dependency provider that constructs and returns the AuthService.
    """
    from app.repositories.repositories import UserRepository, CompanyRepository, RefreshTokenRepository, AuditRepository
    from app.services.services import AuthService, UserService, CompanyService, AuditService
    
    return AuthService(
        db=db,
        user_repo=UserRepository(db),
        company_repo=CompanyRepository(db),
        token_repo=RefreshTokenRepository(db),
        audit_service=AuditService(AuditRepository(db)),
        user_service=UserService(UserRepository(db)),
        company_service=CompanyService(CompanyRepository(db))
    )

