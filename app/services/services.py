from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
import uuid

from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.core.exceptions import (
    InvalidCredentialsException,
    ExpiredTokenException,
    InvalidTokenException,
    PermissionDeniedException,
    UserInactiveException,
    CompanyInactiveException,
    DuplicateResourceException,
    BusinessRuleException,
    NotFoundException
)
from app.utils.validators import (
    validate_email,
    validate_password_strength,
    validate_wallet_address,
    validate_uuid
)
from app.models.models import (
    Company,
    User,
    Registry,
    CarbonProject,
    ProjectDocument,
    CreditBatch,
    Ownership,
    MarketplaceListing,
    PurchaseOrder,
    Transaction,
    Retirement,
    AuditLog,
    RefreshToken,
    UserRole,
    CompanyStatus,
    BatchStatus,
    ListingStatus,
    PurchaseOrderStatus
)
from app.repositories.repositories import (
    CompanyRepository,
    UserRepository,
    RegistryRepository,
    ProjectRepository,
    DocumentRepository,
    BatchRepository,
    OwnershipRepository,
    MarketplaceRepository,
    OrderRepository,
    TransactionRepository,
    RetirementRepository,
    AuditRepository,
    RefreshTokenRepository
)
from app.services.base import BaseService


# ==============================================================================
# AUDIT SERVICE
# ==============================================================================

class AuditService(BaseService[AuditLog]):
    def __init__(self, repository: AuditRepository) -> None:
        super().__init__(repository)

    def record_event(
        self,
        user_id: Optional[uuid.UUID],
        company_id: Optional[uuid.UUID],
        entity_type: str,
        entity_id: Optional[uuid.UUID],
        action: str,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        Creates an audit log entry in the database.
        """
        def make_serializable(val: Any) -> Any:
            from decimal import Decimal
            if isinstance(val, dict):
                return {k: make_serializable(v) for k, v in val.items()}
            elif isinstance(val, list):
                return [make_serializable(x) for x in val]
            elif isinstance(val, Decimal):
                return float(val)
            return val

        audit_in = {
            "user_id": user_id,
            "company_id": company_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action": action,
            "old_values": make_serializable(old_values),
            "new_values": make_serializable(new_values),
            "ip_address": ip_address,
            "user_agent": user_agent,
            "timestamp": datetime.now(timezone.utc)
        }
        log = self.repository.create(audit_in)
        if entity_type != "AuditLog":
            from app.blockchain.service import BlockchainService
            b_service = BlockchainService()
            b_service.submit_to_blockchain("AuditLog", log.id)
        return log

    def record_login(self, user_id: uuid.UUID, company_id: Optional[uuid.UUID], ip: str, ua: str) -> None:
        self.record_event(user_id, company_id, "User", user_id, "LOGIN", ip_address=ip, user_agent=ua)

    def record_logout(self, user_id: uuid.UUID, company_id: Optional[uuid.UUID], ip: str, ua: str) -> None:
        self.record_event(user_id, company_id, "User", user_id, "LOGOUT", ip_address=ip, user_agent=ua)

    def record_create(self, user_id: uuid.UUID, company_id: Optional[uuid.UUID], entity_type: str, entity_id: uuid.UUID, values: dict) -> None:
        self.record_event(user_id, company_id, entity_type, entity_id, "CREATE", new_values=values)

    def record_update(self, user_id: uuid.UUID, company_id: Optional[uuid.UUID], entity_type: str, entity_id: uuid.UUID, old: dict, new: dict) -> None:
        self.record_event(user_id, company_id, entity_type, entity_id, "UPDATE", old_values=old, new_values=new)

    def record_delete(self, user_id: uuid.UUID, company_id: Optional[uuid.UUID], entity_type: str, entity_id: uuid.UUID, values: dict) -> None:
        self.record_event(user_id, company_id, entity_type, entity_id, "DELETE", old_values=values)

    def record_permission_change(self, admin_id: uuid.UUID, user_id: uuid.UUID, old_role: str, new_role: str) -> None:
        self.record_event(
            admin_id, None, "User", user_id, "ROLE_CHANGE",
            old_values={"role": old_role}, new_values={"role": new_role}
        )

    def record_security_event(self, user_id: Optional[uuid.UUID], details: str, ip: str, ua: str) -> None:
        self.record_event(user_id, None, "Security", None, "BREACH_ATTEMPT", new_values={"details": details}, ip_address=ip, user_agent=ua)

    def list_audit_logs(
        self,
        search: Optional[str] = None,
        filter_company: Optional[uuid.UUID] = None,
        filter_user: Optional[uuid.UUID] = None,
        action: Optional[str] = None,
        start_date: Optional[Any] = None,
        end_date: Optional[Any] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[AuditLog], int]:
        from sqlalchemy import select, or_, func
        from app.models.models import User, Company
        db = self.repository.db
        stmt = select(AuditLog).outerjoin(User, User.id == AuditLog.user_id).outerjoin(Company, Company.id == AuditLog.company_id)
        
        if search:
            stmt = stmt.where(or_(
                AuditLog.entity_type.ilike(f"%{search}%"),
                AuditLog.action.ilike(f"%{search}%"),
                User.first_name.ilike(f"%{search}%"),
                User.last_name.ilike(f"%{search}%"),
                Company.name.ilike(f"%{search}%")
            ))
        if filter_company:
            stmt = stmt.where(AuditLog.company_id == filter_company)
        if filter_user:
            stmt = stmt.where(AuditLog.user_id == filter_user)
        if action:
            stmt = stmt.where(AuditLog.action == action)
        if start_date:
            stmt = stmt.where(AuditLog.timestamp >= start_date)
        if end_date:
            stmt = stmt.where(AuditLog.timestamp <= end_date)
            
        stmt = stmt.order_by(AuditLog.timestamp.desc())
        
        total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar() or 0
        items = list(db.execute(stmt.offset(skip).limit(limit)).scalars().all())
        return items, total


# ==============================================================================
# USER SERVICE
# ==============================================================================

class UserService(BaseService[User]):
    def __init__(self, repository: UserRepository) -> None:
        super().__init__(repository)

    def create_user(self, user_in: dict, company_id: Optional[uuid.UUID] = None) -> User:
        # Validate email
        email = user_in.get("email")
        if not email or not validate_email(email):
            raise BusinessRuleException("Invalid email format")
            
        # Check duplicate
        if self.repository.find_one(email=email):
            raise DuplicateResourceException("A user with this email already exists")

        # Validate password strength
        password = user_in.get("password")
        if not password:
            raise BusinessRuleException("Password is required")
        pwd_failures = validate_password_strength(password)
        if pwd_failures:
            raise BusinessRuleException("Weak password", errors=pwd_failures)

        # Hash password and store
        hashed = get_password_hash(password)
        db_user_in = {
            "email": email,
            "hashed_password": hashed,
            "first_name": user_in.get("first_name"),
            "last_name": user_in.get("last_name"),
            "role": user_in.get("role", UserRole.VIEWER),
            "company_id": company_id,
            "is_active": True
        }
        return self.repository.create(db_user_in)

    def update_profile(self, user_id: uuid.UUID, first_name: str, last_name: str, email: str) -> User:
        user = self.repository.find_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")
            
        if not validate_email(email):
            raise BusinessRuleException("Invalid email format")

        existing_user = self.repository.find_one(email=email)
        if existing_user and existing_user.id != user_id:
            raise DuplicateResourceException("Email domain belongs to another registered user")

        return self.repository.update(user, {"first_name": first_name, "last_name": last_name, "email": email})

    def change_password(self, user_id: uuid.UUID, old_password: str, new_password: str) -> User:
        user = self.repository.find_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")
            
        if not verify_password(old_password, user.hashed_password):
            raise InvalidCredentialsException("Current password verification failed")

        pwd_failures = validate_password_strength(new_password)
        if pwd_failures:
            raise BusinessRuleException("New password does not meet criteria", errors=pwd_failures)

        hashed = get_password_hash(new_password)
        return self.repository.update(user, {"hashed_password": hashed})

    def deactivate_user(self, user_id: uuid.UUID) -> User:
        user = self.repository.find_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")
        return self.repository.update(user, {"is_active": False})

    def reactivate_user(self, user_id: uuid.UUID) -> User:
        user = self.repository.find_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")
        return self.repository.update(user, {"is_active": True})

    def assign_role(self, admin_id: uuid.UUID, user_id: uuid.UUID, new_role: UserRole) -> User:
        user = self.repository.find_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")
        old_role = user.role
        updated_user = self.repository.update(user, {"role": new_role})
        return updated_user


# ==============================================================================
# COMPANY SERVICE
# ==============================================================================

class CompanyService(BaseService[Company]):
    def __init__(self, repository: CompanyRepository, audit_service: Optional[AuditService] = None) -> None:
        super().__init__(repository)
        self.audit_service = audit_service or AuditService(AuditRepository(repository.db))

    def create_company(self, company_in: dict) -> Company:
        name = company_in.get("name")
        reg = company_in.get("registration_number")
        wallet = company_in.get("wallet_address")

        if self.repository.find_one(name=name):
            raise DuplicateResourceException("Company name is already taken")
        if self.repository.find_one(registration_number=reg):
            raise DuplicateResourceException("Registration number is already registered")
        if wallet and not validate_wallet_address(wallet):
            raise BusinessRuleException("Invalid blockchain wallet format")
        if wallet and self.repository.find_one(wallet_address=wallet):
            raise DuplicateResourceException("Wallet address is already registered")

        company_data = {
            "name": name,
            "registration_number": reg,
            "industry": company_in.get("industry"),
            "country": company_in.get("country"),
            "website": company_in.get("website"),
            "wallet_address": wallet,
            "email_domain": company_in.get("email_domain"),
            "status": CompanyStatus.ACTIVE
        }
        company = self.repository.create(company_data)
        self.audit_service.record_event(
            user_id=None,
            company_id=company.id,
            entity_type="Company",
            entity_id=company.id,
            action="Company Created",
            new_values=company_data
        )
        return company

    def update_company(self, company_id: uuid.UUID, update_data: dict) -> Company:
        company = self.repository.find_by_id(company_id)
        if not company:
            raise NotFoundException("Company not found")

        # Exclude read-only values
        update_data.pop("id", None)
        update_data.pop("registration_number", None)

        wallet = update_data.get("wallet_address")
        if wallet:
            if not validate_wallet_address(wallet):
                raise BusinessRuleException("Invalid wallet address format")
            existing = self.repository.find_one(wallet_address=wallet)
            if existing and existing.id != company_id:
                raise DuplicateResourceException("Wallet address is linked to another company profile")

        old_val = {"name": company.name, "industry": company.industry, "website": company.website, "wallet_address": company.wallet_address}
        updated = self.repository.update(company, update_data)
        new_val = {"name": updated.name, "industry": updated.industry, "website": updated.website, "wallet_address": updated.wallet_address}
        self.audit_service.record_event(
            user_id=None,
            company_id=updated.id,
            entity_type="Company",
            entity_id=updated.id,
            action="Company Updated",
            old_values=old_val,
            new_values=new_val
        )
        return updated

    def update_wallet(self, company_id: uuid.UUID, wallet_address: str) -> Company:
        if not validate_wallet_address(wallet_address):
            raise BusinessRuleException("Invalid blockchain wallet format")

        existing = self.repository.find_one(wallet_address=wallet_address)
        if existing and existing.id != company_id:
            raise DuplicateResourceException("Wallet address is linked to another company profile")

        company = self.repository.find_by_id(company_id)
        if not company:
            raise NotFoundException("Company profile not found")

        return self.repository.update(company, {"wallet_address": wallet_address})

    def deactivate_company(self, company_id: uuid.UUID) -> Company:
        company = self.repository.find_by_id(company_id)
        if not company:
            raise NotFoundException("Company not found")
        return self.repository.update(company, {"status": CompanyStatus.INACTIVE})

    def list_users(self, company_id: uuid.UUID) -> List[User]:
        company = self.repository.find_by_id(company_id)
        if not company:
            raise NotFoundException("Company not found")
        return company.users


# ==============================================================================
# AUTH SERVICE
# ==============================================================================

class AuthService:
    """
    Orchestration service handling User Registration, Authentication,
    and Refresh Token Rotation (RTR) family tracking.
    """
    def __init__(
        self,
        db: Session,
        user_repo: UserRepository,
        company_repo: CompanyRepository,
        token_repo: RefreshTokenRepository,
        audit_service: AuditService,
        user_service: UserService,
        company_service: CompanyService
    ) -> None:
        self.db = db
        self.user_repo = user_repo
        self.company_repo = company_repo
        self.token_repo = token_repo
        self.audit_service = audit_service
        self.user_service = user_service
        self.company_service = company_service

    def register_company_and_admin(self, reg_data: dict) -> Tuple[User, Company, str, str]:
        """
        Executes a transactional registration: Creates a Company profile
        and registers a COMPANY_ADMIN user under that company.
        """
        # Start transaction explicitly
        company_in = {
            "name": reg_data["company_name"],
            "registration_number": reg_data["registration_number"],
            "country": reg_data["country"],
            "industry": reg_data.get("industry"),
            "website": reg_data.get("website"),
            "wallet_address": reg_data.get("wallet_address")
        }
        
        # 1. Create company profile
        company = self.company_service.create_company(company_in)

        # 2. Create company admin user
        user_in = {
            "email": reg_data["email"],
            "first_name": reg_data["first_name"],
            "last_name": reg_data["last_name"],
            "password": reg_data["password"],
            "role": UserRole.COMPANY_ADMIN
        }
        user = self.user_service.create_user(user_in, company_id=company.id)

        # 3. Generate initial token pair
        access_token, _ = create_access_token(user.id, user.role, company.id)
        refresh_token, refresh_jti = create_refresh_token(user.id, user.role, company.id)

        # 4. Save refresh token in database
        self.token_repo.create({
            "token_jti": refresh_jti,
            "user_id": user.id,
            "expires_at": datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            "is_revoked": False
        })

        # Record audit log
        self.audit_service.record_create(
            user.id, company.id, "Company", company.id, {"name": company.name}
        )
        self.audit_service.record_create(
            user.id, company.id, "User", user.id, {"email": user.email}
        )
        self.audit_service.record_event(
            user_id=user.id,
            company_id=company.id,
            entity_type="User",
            entity_id=user.id,
            action="Register",
            new_values={"email": user.email, "company_name": company.name}
        )

        return user, company, access_token, refresh_token

    def login_user(self, login_data: dict, ip: str, ua: str) -> Tuple[User, Optional[Company], str, str]:
        email = login_data.get("email")
        password = login_data.get("password")

        user = self.user_repo.find_one(email=email)
        if not user or not verify_password(password, user.hashed_password):
            self.audit_service.record_security_event(None, f"Failed login attempt for email {email}", ip, ua)
            raise InvalidCredentialsException("Invalid email or password")

        if not user.is_active:
            raise UserInactiveException("User account is inactive. Please contact support.")

        company = None
        if user.company_id:
            company = self.company_repo.find_by_id(user.company_id)
            if not company:
                raise CompanyInactiveException("Associated company profile does not exist.")
            if company.status != CompanyStatus.ACTIVE:
                raise CompanyInactiveException(f"Associated company status is {company.status}")

        # Generate tokens
        comp_id = company.id if company else None
        access_token, _ = create_access_token(user.id, user.role, comp_id)
        refresh_token, refresh_jti = create_refresh_token(user.id, user.role, comp_id)

        # Save refresh token
        self.token_repo.create({
            "token_jti": refresh_jti,
            "user_id": user.id,
            "expires_at": datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            "is_revoked": False
        })

        self.audit_service.record_login(user.id, comp_id, ip, ua)
        return user, company, access_token, refresh_token

    def refresh_access_tokens(self, refresh_token: str, ip: str, ua: str) -> Tuple[str, str]:
        """
        Validates refresh token. Implements Refresh Token Rotation (RTR).
        Detects token reuse: if a revoked refresh token is presented,
        invalidates all active refresh tokens for the user (breach containment).
        """
        payload = decode_token(refresh_token)
        user_id_str = payload.get("sub")
        token_jti = payload.get("jti")
        token_type = payload.get("type")

        if not user_id_str or token_type != "refresh" or not token_jti:
            raise InvalidTokenException("Invalid refresh token credentials")

        user_id = uuid.UUID(user_id_str)
        user = self.user_repo.find_by_id(user_id)
        if not user or not user.is_active:
            raise UserInactiveException("Associated user account is deactivated")

        # Find token record in database
        db_token = self.token_repo.find_one(token_jti=token_jti)
        if not db_token:
            raise InvalidTokenException("Refresh token is unrecognized")

        # Breach Detection: Check if token has been revoked
        if db_token.is_revoked:
            # Token reuse detected! Log security breach.
            self.audit_service.record_security_event(
                user.id,
                f"Breach detected: Reused refresh token JTI {token_jti}. Revoking user session.",
                ip, ua
            )
            # Invalidate all active tokens for this user (compromise recovery)
            active_tokens = self.token_repo.find_many(user_id=user_id, is_revoked=False)
            for active_t in active_tokens:
                self.token_repo.update(active_t, {"is_revoked": True})
                
            # Log reuse timestamp for audit trail
            self.token_repo.update(db_token, {"reused_at": datetime.now(timezone.utc)})
            raise PermissionDeniedException("Security alert: Access token compromise detected. Please re-authenticate.")

        expires_at = db_token.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at < datetime.now(timezone.utc):
            raise ExpiredTokenException("Session expired. Please log in again.")

        # Invalidate/revoke current token
        self.token_repo.update(db_token, {"is_revoked": True})

        # Generate new token family link
        comp_id = user.company_id if user.company_id else None
        new_access_token, _ = create_access_token(user.id, user.role, comp_id)
        new_refresh_token, new_jti = create_refresh_token(user.id, user.role, comp_id)

        # Save new refresh token JTI
        self.token_repo.create({
            "token_jti": new_jti,
            "user_id": user.id,
            "expires_at": datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            "is_revoked": False
        })

        return new_access_token, new_refresh_token

    def logout_user(self, refresh_token: str, current_user_id: uuid.UUID, ip: str, ua: str) -> None:
        """
        Logs a user out by blacklisting/revoking the presented refresh token.
        """
        try:
            payload = decode_token(refresh_token)
            token_jti = payload.get("jti")
            
            if token_jti:
                db_token = self.token_repo.find_one(token_jti=token_jti)
                if db_token and db_token.user_id == current_user_id:
                    self.token_repo.update(db_token, {"is_revoked": True})
        except Exception:
            # We fail silently for decoding errors during logout to guarantee clean logout interface
            pass

        self.audit_service.record_logout(
            current_user_id,
            self.user_repo.find_by_id(current_user_id).company_id,
            ip, ua
        )


# ==============================================================================
# SUBCLASS STUBS FOR COMPILATION
# ==============================================================================

class RegistryService(BaseService[Registry]):
    def __init__(self, repository: RegistryRepository, audit_service: Optional[AuditService] = None) -> None:
        super().__init__(repository)
        from app.repositories.repositories import AuditRepository
        self.audit_service = audit_service or AuditService(AuditRepository(repository.db))

    def create_registry(self, data: dict, admin_id: uuid.UUID) -> Registry:
        self.validate_registry(data)
        
        # Check uniqueness
        if self.repository.find_by_name(data["name"]):
            raise DuplicateResourceException(f"Registry with name '{data['name']}' already exists")
            
        registry = self.repository.create(data)
        
        self.audit_service.record_event(
            user_id=admin_id,
            company_id=None,
            entity_type="Registry",
            entity_id=registry.id,
            action="Registry Created",
            new_values={"name": registry.name, "status": registry.status}
        )
        return registry

    def update_registry(self, registry_id: uuid.UUID, data: dict, admin_id: uuid.UUID) -> Registry:
        registry = self.repository.find_by_id(registry_id)
        if not registry:
            raise NotFoundException(f"Registry with ID {registry_id} not found")
            
        if "name" in data and data["name"] != registry.name:
            if self.repository.find_by_name(data["name"]):
                raise DuplicateResourceException(f"Registry with name '{data['name']}' already exists")
                
        if "website" in data:
            if not data["website"].startswith(("http://", "https://")):
                raise BusinessRuleException("Invalid website URL format")

        old_values = {"name": registry.name, "website": registry.website, "status": registry.status}
        updated = self.repository.update(registry, data)
        new_values = {"name": updated.name, "website": updated.website, "status": updated.status}
        
        self.audit_service.record_update(
            admin_id, None, "Registry", updated.id, old_values, new_values
        )
        return updated

    def get_registry(self, registry_id: uuid.UUID) -> Registry:
        registry = self.repository.find_by_id(registry_id)
        if not registry:
            raise NotFoundException(f"Registry with ID {registry_id} not found")
        return registry

    def list_registries(self) -> List[Registry]:
        return self.repository.find_many()

    def search_registries(
        self,
        search_query: Optional[str] = None,
        status: Optional[str] = None,
        country: Optional[str] = None,
        accreditation: Optional[str] = None,
        page: int = 1,
        limit: int = 100,
        sort: Optional[str] = None,
        order: str = "asc"
    ) -> Tuple[List[Registry], int]:
        skip = (page - 1) * limit
        return self.repository.search(
            search_query=search_query,
            status=status,
            country=country,
            accreditation=accreditation,
            skip=skip,
            limit=limit,
            sort_field=sort,
            sort_order=order
        )

    def activate_registry(self, registry_id: uuid.UUID, admin_id: uuid.UUID) -> Registry:
        return self.update_registry(registry_id, {"status": "ACTIVE"}, admin_id)

    def deactivate_registry(self, registry_id: uuid.UUID, admin_id: uuid.UUID) -> Registry:
        return self.update_registry(registry_id, {"status": "INACTIVE"}, admin_id)

    def delete_registry(self, registry_id: uuid.UUID, admin_id: uuid.UUID) -> Registry:
        registry = self.repository.find_by_id(registry_id)
        if not registry:
            raise NotFoundException(f"Registry with ID {registry_id} not found")
            
        deleted = self.repository.soft_delete(registry)
        
        self.audit_service.record_delete(
            admin_id, None, "Registry", registry.id, {"name": registry.name, "deleted_at": str(deleted.deleted_at)}
        )
        return deleted

    def validate_registry(self, data: dict) -> None:
        if not data.get("name"):
            raise BusinessRuleException("Registry name is required")
        if not data.get("website") or not data["website"].startswith(("http://", "https://")):
            raise BusinessRuleException("Valid website URL is required")
        if not data.get("country"):
            raise BusinessRuleException("Registry country is required")
        if not data.get("accreditation"):
            raise BusinessRuleException("Registry accreditation details are required")

    def get_registry_statistics(self, registry_id: uuid.UUID) -> dict:
        # Check existence
        self.get_registry(registry_id)
        
        db = self.repository.db
        from sqlalchemy import select, func
        
        # Projects count
        proj_stmt = select(CarbonProject).where(CarbonProject.registry_id == registry_id, CarbonProject.deleted_at == None)
        projects = db.execute(proj_stmt).scalars().all()
        projects_count = len(projects)
        active_projects = sum(1 for p in projects if p.status == "ACTIVE")
        inactive_projects = projects_count - active_projects

        # Credit batches count & total credits issued
        batches_stmt = select(CreditBatch).join(CarbonProject).where(CarbonProject.registry_id == registry_id, CarbonProject.deleted_at == None)
        batches = db.execute(batches_stmt).scalars().all()
        batches_count = len(batches)
        total_credits_issued = float(sum(b.total_credits for b in batches))

        return {
            "projects_count": projects_count,
            "batches_count": batches_count,
            "total_credits_issued": total_credits_issued,
            "active_projects": active_projects,
            "inactive_projects": inactive_projects
        }


class ProjectService(BaseService[CarbonProject]):
    def __init__(
        self,
        repository: ProjectRepository,
        registry_repository: Optional[RegistryRepository] = None,
        audit_service: Optional[AuditService] = None
    ) -> None:
        super().__init__(repository)
        from app.repositories.repositories import RegistryRepository as RegRepo, AuditRepository as AuditRepo
        self.registry_repository = registry_repository or RegRepo(repository.db)
        self.audit_service = audit_service or AuditService(AuditRepo(repository.db))

    def create_project(self, data: dict, admin_id: uuid.UUID) -> CarbonProject:
        self.validate_project(data)
        
        # Check unique code
        if self.repository.find_by_project_code(data["project_code"]):
            raise DuplicateResourceException(f"Project code '{data['project_code']}' is already registered")

        # Check registry exists
        registry = self.registry_repository.find_by_id(data["registry_id"])
        if not registry:
            raise NotFoundException(f"Registry with ID {data['registry_id']} not found")

        project = self.repository.create(data)
        
        self.audit_service.record_event(
            user_id=admin_id,
            company_id=None,
            entity_type="Project",
            entity_id=project.id,
            action="Project Created",
            new_values={"name": project.name, "code": project.project_code}
        )
        return project

    def update_project(self, project_id: uuid.UUID, data: dict, admin_id: uuid.UUID) -> CarbonProject:
        project = self.repository.find_by_id(project_id)
        if not project:
            raise NotFoundException(f"Project with ID {project_id} not found")

        if "project_code" in data and data["project_code"] != project.project_code:
            if self.repository.find_by_project_code(data["project_code"]):
                raise DuplicateResourceException(f"Project code '{data['project_code']}' is already registered")

        if "registry_id" in data:
            registry = self.registry_repository.find_by_id(data["registry_id"])
            if not registry:
                raise NotFoundException(f"Registry with ID {data['registry_id']} not found")

        # Validate date sequence if updating dates
        start = data.get("start_date", project.start_date)
        end = data.get("end_date", project.end_date)
        if end < start:
            raise BusinessRuleException("Project end date cannot be before start date")

        old_values = {"name": project.name, "code": project.project_code, "status": project.status}
        updated = self.repository.update(project, data)
        new_values = {"name": updated.name, "code": updated.project_code, "status": updated.status}
        
        self.audit_service.record_update(
            admin_id, None, "Project", updated.id, old_values, new_values
        )
        return updated

    def delete_project(self, project_id: uuid.UUID, admin_id: uuid.UUID) -> CarbonProject:
        project = self.repository.find_by_id(project_id)
        if not project:
            raise NotFoundException(f"Project with ID {project_id} not found")
            
        deleted = self.repository.soft_delete(project)
        
        self.audit_service.record_delete(
            admin_id, None, "Project", project.id, {"name": project.name, "deleted_at": str(deleted.deleted_at)}
        )
        return deleted

    def get_project(self, project_id: uuid.UUID) -> CarbonProject:
        project = self.repository.find_by_id(project_id)
        if not project:
            raise NotFoundException(f"Project with ID {project_id} not found")
        return project

    def list_projects(self) -> List[CarbonProject]:
        return self.repository.find_many()

    def search_projects(
        self,
        search_query: Optional[str] = None,
        country: Optional[str] = None,
        registry_id: Optional[str] = None,
        verification_standard: Optional[str] = None,
        project_type: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        limit: int = 100,
        sort: Optional[str] = None,
        order: str = "asc"
    ) -> Tuple[List[CarbonProject], int]:
        skip = (page - 1) * limit
        return self.repository.search(
            search_query=search_query,
            country=country,
            registry_id=registry_id,
            verification_standard=verification_standard,
            project_type=project_type,
            status=status,
            skip=skip,
            limit=limit,
            sort_field=sort,
            sort_order=order
        )

    def assign_registry(self, project_id: uuid.UUID, registry_id: uuid.UUID, admin_id: uuid.UUID) -> CarbonProject:
        return self.update_project(project_id, {"registry_id": registry_id}, admin_id)

    def validate_project(self, data: dict) -> None:
        if not data.get("project_code"):
            raise BusinessRuleException("Project code is required")
        if not data.get("registry_id"):
            raise BusinessRuleException("Registry ID association is required")
        if not data.get("name"):
            raise BusinessRuleException("Project name is required")
        if not data.get("country"):
            raise BusinessRuleException("Project location country is required")
        if not data.get("project_type"):
            raise BusinessRuleException("Project type is required")
        if not data.get("verification_standard"):
            raise BusinessRuleException("Verification standard is required")
        if not data.get("developer"):
            raise BusinessRuleException("Project developer is required")
            
        start = data.get("start_date")
        end = data.get("end_date")
        if not start or not end:
            raise BusinessRuleException("Project start and end dates are required")
        if end < start:
            raise BusinessRuleException("Project end date cannot be before start date")

    def get_project_statistics(self, project_id: uuid.UUID) -> dict:
        # Check existence
        self.get_project(project_id)
        
        db = self.repository.db
        from sqlalchemy import select, func
        from app.models.models import CreditBatch, Retirement, Ownership

        # Batches count & Total credits issued/remaining
        batch_stmt = select(
            func.count(CreditBatch.id),
            func.sum(CreditBatch.total_credits),
            func.sum(CreditBatch.remaining_credits)
        ).where(CreditBatch.project_id == project_id)
        
        result = db.execute(batch_stmt).first()
        batches_count = result[0] or 0
        credits_issued = float(result[1] or 0.0)
        credits_remaining = float(result[2] or 0.0)

        # Retired credits
        retired_stmt = select(func.sum(Retirement.credits_retired))\
            .join(Ownership)\
            .join(CreditBatch)\
            .where(CreditBatch.project_id == project_id)
        credits_retired = float(db.execute(retired_stmt).scalar() or 0.0)

        # Unique holding companies count
        holding_stmt = select(func.count(func.distinct(Ownership.company_id)))\
            .join(CreditBatch)\
            .where(CreditBatch.project_id == project_id, Ownership.owned_credits > 0)
        companies_holding_count = int(db.execute(holding_stmt).scalar() or 0)

        return {
            "batches_count": batches_count,
            "credits_issued": credits_issued,
            "credits_remaining": credits_remaining,
            "credits_retired": credits_retired,
            "companies_holding_count": companies_holding_count
        }


class DocumentService(BaseService[ProjectDocument]):
    def __init__(
        self,
        repository: DocumentRepository,
        project_repository: Optional[ProjectRepository] = None,
        audit_service: Optional[AuditService] = None
    ) -> None:
        super().__init__(repository)
        from app.repositories.repositories import ProjectRepository as ProjRepo, AuditRepository as AuditRepo
        self.project_repository = project_repository or ProjRepo(repository.db)
        self.audit_service = audit_service or AuditService(AuditRepo(repository.db))

    def add_document(self, project_id: uuid.UUID, data: dict, admin_id: uuid.UUID) -> ProjectDocument:
        # Check project exists
        project = self.project_repository.find_by_id(project_id)
        if not project:
            raise NotFoundException(f"Project with ID {project_id} not found")

        doc_data = {
            "project_id": project_id,
            "document_type": data["document_type"],
            "file_name": data["file_name"],
            "file_url": data["file_url"]
        }
        document = self.repository.create(doc_data)
        
        self.audit_service.record_create(
            admin_id, None, "Document", document.id, {"file_name": document.file_name, "project_id": str(project_id)}
        )
        return document

    def update_document(self, document_id: uuid.UUID, data: dict, admin_id: uuid.UUID) -> ProjectDocument:
        document = self.repository.find_by_id(document_id)
        if not document:
            raise NotFoundException(f"Document with ID {document_id} not found")

        old_values = {"file_name": document.file_name, "type": document.document_type.value}
        updated = self.repository.update(document, data)
        new_values = {"file_name": updated.file_name, "type": updated.document_type.value}
        
        self.audit_service.record_update(
            admin_id, None, "Document", updated.id, old_values, new_values
        )
        return updated

    def delete_document(self, document_id: uuid.UUID, admin_id: uuid.UUID) -> None:
        document = self.repository.find_by_id(document_id)
        if not document:
            raise NotFoundException(f"Document with ID {document_id} not found")
            
        self.repository.delete(document)
        
        self.audit_service.record_delete(
            admin_id, None, "Document", document.id, {"file_name": document.file_name}
        )

    def list_project_documents(self, project_id: uuid.UUID) -> List[ProjectDocument]:
        return self.repository.find_by_project(project_id)




class BatchService(BaseService[CreditBatch]):
    def __init__(
        self,
        repository: BatchRepository,
        project_repository: Optional[ProjectRepository] = None,
        audit_service: Optional[AuditService] = None,
        ownership_service: Optional[Any] = None
    ) -> None:
        super().__init__(repository)
        from app.repositories.repositories import ProjectRepository as ProjRepo, AuditRepository as AuditRepo
        self.project_repository = project_repository or ProjRepo(repository.db)
        self.audit_service = audit_service or AuditService(AuditRepo(repository.db))
        self._ownership_service = ownership_service

    @property
    def ownership_service(self):
        if not self._ownership_service:
            from app.repositories.repositories import OwnershipRepository
            self._ownership_service = OwnershipService(OwnershipRepository(self.repository.db))
        return self._ownership_service

    def create_batch(self, data: dict, admin_id: uuid.UUID) -> CreditBatch:
        self.validate_batch(data)
        
        # Check uniqueness
        if self.repository.find_by_batch_number(data["batch_number"]):
            raise DuplicateResourceException(f"Batch number '{data['batch_number']}' already exists")
            
        # Check project exists
        project = self.project_repository.find_by_id(data["project_id"])
        if not project:
            raise NotFoundException(f"Carbon project with ID {data['project_id']} not found")
            
        # Initial status
        data.setdefault("status", "ACTIVE")
        
        # Extract initial company owner if passed in data
        initial_company_id = data.pop("company_id", None)
        
        # Create credit batch
        batch = self.repository.create(data)
        
        # If company_id is provided, create initial ownership
        if initial_company_id:
            self.ownership_service.create_ownership({
                "batch_id": batch.id,
                "company_id": initial_company_id,
                "owned_credits": batch.total_credits,
                "average_purchase_price": 0.0
            })

        self.audit_service.record_event(
            user_id=admin_id,
            company_id=None,
            entity_type="CreditBatch",
            entity_id=batch.id,
            action="Batch Created",
            new_values={"batch_number": batch.batch_number, "total_credits": batch.total_credits}
        )
        
        # Trigger on-chain registry
        from app.blockchain.service import BlockchainService
        b_service = BlockchainService()
        b_service.submit_to_blockchain("CreditBatch", batch.id)
        
        return batch

    def update_batch(self, batch_id: uuid.UUID, data: dict, admin_id: uuid.UUID) -> CreditBatch:
        batch = self.repository.find_by_id(batch_id)
        if not batch:
            raise NotFoundException(f"Credit batch with ID {batch_id} not found")
            
        allowed_keys = {"status", "metadata_json"}
        forbidden_keys = set(data.keys()) - allowed_keys
        if forbidden_keys:
            raise BusinessRuleException(f"Cannot update immutable fields: {', '.join(forbidden_keys)}")
            
        if "status" in data:
            self.validate_status_transition(batch.status, data["status"])
            self.audit_service.record_event(
                admin_id, None, "CreditBatch", batch.id, "STATUS_CHANGED",
                old_values={"old_status": batch.status},
                new_values={"new_status": data["status"]}
            )
            
        old_vals = {"status": batch.status, "metadata": batch.metadata_json}
        updated = self.repository.update(batch, data)
        new_vals = {"status": updated.status, "metadata": updated.metadata_json}
        
        self.audit_service.record_update(
            admin_id, None, "CreditBatch", updated.id, old_vals, new_vals
        )
        return updated

    def change_status(self, batch_id: uuid.UUID, new_status: str, admin_id: uuid.UUID) -> CreditBatch:
        return self.update_batch(batch_id, {"status": new_status}, admin_id)

    def get_batch(self, batch_id: uuid.UUID) -> CreditBatch:
        batch = self.repository.find_by_id(batch_id)
        if not batch:
            raise NotFoundException(f"Credit batch with ID {batch_id} not found")
        return batch

    def list_batches(self) -> List[CreditBatch]:
        return self.repository.find_many()

    def search_batches(
        self,
        search_query: Optional[str] = None,
        registry_id: Optional[str] = None,
        country: Optional[str] = None,
        project_type: Optional[str] = None,
        verification_standard: Optional[str] = None,
        vintage_year: Optional[int] = None,
        status: Optional[str] = None,
        page: int = 1,
        limit: int = 100,
        sort: Optional[str] = None,
        order: str = "asc"
    ) -> Tuple[List[CreditBatch], int]:
        skip = (page - 1) * limit
        return self.repository.search(
            search_query=search_query,
            registry_id=registry_id,
            country=country,
            project_type=project_type,
            verification_standard=verification_standard,
            vintage_year=vintage_year,
            status=status,
            skip=skip,
            limit=limit,
            sort_field=sort,
            sort_order=order
        )

    def validate_batch(self, data: dict) -> None:
        if not data.get("batch_number"):
            raise BusinessRuleException("Batch number is required")
        if not data.get("project_id"):
            raise BusinessRuleException("Associated project ID is required")
            
        vintage = data.get("vintage_year")
        if vintage is None:
            raise BusinessRuleException("Vintage year is required")
        import datetime
        current_year = datetime.datetime.now().year
        if vintage > current_year:
            raise BusinessRuleException(f"Vintage year {vintage} cannot be greater than the current year {current_year}")
            
        total = data.get("total_credits")
        if total is None or total <= 0:
            raise BusinessRuleException("Total credits must be greater than zero")
            
        remaining = data.get("remaining_credits", total)
        if remaining > total:
            raise BusinessRuleException("Remaining credits cannot exceed total credits")
        if remaining < 0:
            raise BusinessRuleException("Remaining credits cannot be negative")

    def validate_status_transition(self, old_status: str, new_status: str) -> None:
        valid_statuses = {"ACTIVE", "PARTIALLY_USED", "RETIRED", "EXPIRED"}
        if new_status not in valid_statuses:
            raise BusinessRuleException(f"Invalid target status: '{new_status}'")
            
        if old_status == new_status:
            return
            
        if old_status in ("RETIRED", "EXPIRED"):
            raise BusinessRuleException(f"Cannot transition from terminal status '{old_status}' to '{new_status}'")

    def get_batch_statistics(self, batch_id: uuid.UUID) -> dict:
        batch = self.get_batch(batch_id)
        
        db = self.repository.db
        from sqlalchemy import select, func
        from app.models.models import Retirement, Ownership
        
        retired_stmt = select(func.sum(Retirement.credits_retired))\
            .join(Ownership)\
            .where(Ownership.batch_id == batch_id)
        retired_credits = float(db.execute(retired_stmt).scalar() or 0.0)
        
        owners_stmt = select(func.count(func.distinct(Ownership.company_id)))\
            .where(Ownership.batch_id == batch_id, Ownership.owned_credits > 0)
        owners_count = int(db.execute(owners_stmt).scalar() or 0)
        
        return {
            "total_credits": batch.total_credits,
            "remaining_credits": batch.remaining_credits,
            "retired_credits": retired_credits,
            "unique_owners_count": owners_count
        }


class OwnershipService(BaseService[Ownership]):
    def __init__(
        self,
        repository: OwnershipRepository,
        batch_repository: Optional[BatchRepository] = None,
        company_repository: Optional[CompanyRepository] = None,
        audit_service: Optional[AuditService] = None
    ) -> None:
        super().__init__(repository)
        from app.repositories.repositories import BatchRepository as BatchRepo, CompanyRepository as CompRepo, AuditRepository as AuditRepo
        self.batch_repository = batch_repository or BatchRepo(repository.db)
        self.company_repository = company_repository or CompRepo(repository.db)
        self.audit_service = audit_service or AuditService(AuditRepo(repository.db))

    def create_ownership(self, data: dict) -> Ownership:
        self.validate_ownership(data)
        
        batch_uuid = uuid.UUID(str(data["batch_id"]))
        company_uuid = uuid.UUID(str(data["company_id"]))
        
        from sqlalchemy import select
        stmt = select(Ownership).where(Ownership.batch_id == batch_uuid, Ownership.company_id == company_uuid)
        existing = self.repository.db.execute(stmt).scalar_one_or_none()
        
        if existing:
            old_credits = existing.owned_credits
            existing.owned_credits += float(data["owned_credits"])
            self.repository.db.commit()
            
            self.audit_service.record_event(
                existing.company_id, None, "Ownership", existing.id, "OWNERSHIP_UPDATED",
                old_values={"old_credits": old_credits},
                new_values={"new_credits": existing.owned_credits}
            )
            return existing
            
        ownership = self.repository.create(data)
        
        self.audit_service.record_event(
            ownership.company_id, None, "Ownership", ownership.id, "OWNERSHIP_CREATED",
            new_values={"batch_id": str(ownership.batch_id), "owned_credits": ownership.owned_credits}
        )
        return ownership

    def update_ownership(self, ownership_id: uuid.UUID, data: dict, admin_id: uuid.UUID) -> Ownership:
        ownership = self.repository.find_by_id(ownership_id)
        if not ownership:
            raise NotFoundException(f"Ownership record with ID {ownership_id} not found")
            
        old_credits = ownership.owned_credits
        updated = self.repository.update(ownership, data)
        
        self.audit_service.record_event(
            admin_id, None, "Ownership", updated.id, "OWNERSHIP_UPDATED",
            old_values={"old_credits": old_credits},
            new_values={"new_credits": updated.owned_credits}
        )
        return updated

    def transfer_ownership(
        self,
        from_company_id: uuid.UUID,
        to_company_id: uuid.UUID,
        batch_id: uuid.UUID,
        credits: float,
        price_per_credit: float,
        session: Session
    ) -> Tuple[Ownership, Ownership]:
        if credits <= 0:
            raise BusinessRuleException("Transfer credits must be greater than zero")
            
        from sqlalchemy import select
        stmt_from = select(Ownership).where(Ownership.company_id == from_company_id, Ownership.batch_id == batch_id)
        sender_ownership = session.execute(stmt_from).scalar_one_or_none()
        
        if not sender_ownership or float(sender_ownership.owned_credits) < credits:
            raise BusinessRuleException("Sender has insufficient credits in this batch to complete transfer")
            
        stmt_to = select(Ownership).where(Ownership.company_id == to_company_id, Ownership.batch_id == batch_id)
        recipient_ownership = session.execute(stmt_to).scalar_one_or_none()
        
        sender_old_credits = float(sender_ownership.owned_credits)
        sender_ownership.owned_credits = float(sender_old_credits - credits)
        
        if recipient_ownership:
            current_owned = float(recipient_ownership.owned_credits)
            current_average = float(recipient_ownership.average_purchase_price or 0.0)
            
            recipient_old_credits = current_owned
            recipient_ownership.owned_credits = float(current_owned + credits)
            
            if (current_owned + credits) > 0:
                new_average = ((current_owned * current_average) + (credits * price_per_credit)) / (current_owned + credits)
                recipient_ownership.average_purchase_price = float(new_average)
        else:
            recipient_old_credits = 0.0
            recipient_ownership = Ownership(
                id=uuid.uuid4(),
                company_id=to_company_id,
                batch_id=batch_id,
                owned_credits=credits,
                average_purchase_price=float(price_per_credit)
            )
            session.add(recipient_ownership)
            
        session.flush()
        
        self.audit_service.record_event(
            from_company_id, None, "Ownership", sender_ownership.id, "OWNERSHIP_TRANSFER",
            new_values={
                "to_company_id": str(to_company_id),
                "batch_id": str(batch_id),
                "credits": credits,
                "price_per_credit": price_per_credit
            }
        )
        return sender_ownership, recipient_ownership

    def get_company_ownerships(self, company_id: uuid.UUID) -> List[Ownership]:
        return self.repository.find_by_company(company_id)

    def get_batch_ownerships(self, batch_id: uuid.UUID) -> List[Ownership]:
        return self.repository.find_by_batch(batch_id)

    def calculate_total_owned(self, batch_id: uuid.UUID) -> float:
        db = self.repository.db
        from sqlalchemy import select, func
        stmt = select(func.sum(Ownership.owned_credits)).where(Ownership.batch_id == batch_id)
        return float(db.execute(stmt).scalar() or 0.0)

    def calculate_available_credits(self, company_id: uuid.UUID) -> float:
        ownerships = self.get_company_ownerships(company_id)
        total_available = 0.0
        db = self.repository.db
        from sqlalchemy import select, func
        from app.models.models import MarketplaceListing
        
        for own in ownerships:
            listing_stmt = select(func.sum(MarketplaceListing.credits_for_sale))\
                .where(
                    MarketplaceListing.ownership_id == own.id,
                    MarketplaceListing.status.in_(["PUBLISHED", "PENDING", "UNDER_REVIEW"])
                )
            listed_credits = float(db.execute(listing_stmt).scalar() or 0.0)
            total_available += max(0.0, own.owned_credits - listed_credits)
            
        return total_available

    def validate_ownership(self, data: dict) -> None:
        batch_id = data.get("batch_id")
        company_id = data.get("company_id")
        owned = data.get("owned_credits")
        
        if not batch_id or not company_id:
            raise BusinessRuleException("Batch ID and Company ID are required")
            
        if owned is None or owned <= 0:
            raise BusinessRuleException("Owned credits must be greater than zero")
            
        batch = self.batch_repository.find_by_id(batch_id)
        if not batch:
            raise NotFoundException(f"Credit batch with ID {batch_id} not found")
            
        company = self.company_repository.find_by_id(company_id)
        if not company:
            raise NotFoundException(f"Company with ID {company_id} not found")
            
        current_total = self.calculate_total_owned(batch_id)
        from sqlalchemy import select
        stmt = select(Ownership).where(Ownership.batch_id == batch_id, Ownership.company_id == company_id)
        existing = self.repository.db.execute(stmt).scalar_one_or_none()
        
        existing_owned = existing.owned_credits if existing else 0.0
        if (current_total - existing_owned + owned) > batch.total_credits:
            raise BusinessRuleException("The total owned credits for a batch cannot exceed the batch's total credits limit")


class PortfolioService:
    def __init__(
        self,
        db: Session,
        ownership_service: Optional[OwnershipService] = None,
        company_repository: Optional[CompanyRepository] = None,
        audit_service: Optional[AuditService] = None
    ) -> None:
        self.db = db
        from app.repositories.repositories import OwnershipRepository, CompanyRepository as CompRepo, AuditRepository as AuditRepo
        self.ownership_service = ownership_service or OwnershipService(OwnershipRepository(db))
        self.company_repository = company_repository or CompRepo(db)
        self.audit_service = audit_service or AuditService(AuditRepo(db))

    def get_portfolio(self, company_id: uuid.UUID) -> dict:
        company = self.company_repository.find_by_id(company_id)
        if not company:
            raise NotFoundException(f"Company with ID {company_id} not found")
            
        stats = self.get_statistics(company_id)
        batches = self.get_owned_batches(company_id)
        
        self.audit_service.record_event(
            None, company_id, "Portfolio", company_id, "PORTFOLIO_VIEWED",
            new_values={"owned_credit_count": stats["owned_credit_count"]}
        )
        
        return {
            "company": {
                "id": company.id,
                "name": company.name,
                "registration_number": company.registration_number,
                "wallet_address": company.wallet_address
            },
            "portfolio_summary": stats,
            "owned_batches": batches
        }

    def get_statistics(self, company_id: uuid.UUID) -> dict:
        ownerships = self.ownership_service.get_company_ownerships(company_id)
        owned_credit_count = float(sum(o.owned_credits for o in ownerships))
        
        from sqlalchemy import select, func
        from app.models.models import MarketplaceListing, Retirement
        
        listed_credit_count = 0.0
        for own in ownerships:
            listing_stmt = select(func.sum(MarketplaceListing.credits_for_sale))\
                .where(
                    MarketplaceListing.ownership_id == own.id,
                    MarketplaceListing.status.in_(["PUBLISHED", "PENDING", "UNDER_REVIEW"])
                )
            listed_credit_count += float(self.db.execute(listing_stmt).scalar() or 0.0)
            
        available_credit_count = max(0.0, owned_credit_count - listed_credit_count)
        
        retired_stmt = select(func.sum(Retirement.credits_retired))\
            .join(Ownership)\
            .where(Ownership.company_id == company_id)
        retired_credit_count = float(self.db.execute(retired_stmt).scalar() or 0.0)
        
        estimated_portfolio_value = float(sum(
            float(o.owned_credits) * float(o.average_purchase_price or 0.0) for o in ownerships
        ))
        
        return {
            "owned_credit_count": float(owned_credit_count),
            "available_credit_count": float(available_credit_count),
            "listed_credit_count": float(listed_credit_count),
            "retired_credit_count": float(retired_credit_count),
            "estimated_portfolio_value": float(estimated_portfolio_value)
        }

    def get_owned_batches(self, company_id: uuid.UUID) -> List[dict]:
        ownerships = self.ownership_service.get_company_ownerships(company_id)
        
        owned_batches_data = []
        for own in ownerships:
            if own.owned_credits <= 0:
                continue
                
            batch = own.batch
            if not batch:
                continue
                
            project = batch.project
            registry = project.registry if project else None
            
            from sqlalchemy import select, func
            from app.models.models import MarketplaceListing
            listing_stmt = select(func.sum(MarketplaceListing.credits_for_sale))\
                .where(
                    MarketplaceListing.ownership_id == own.id,
                    MarketplaceListing.status.in_(["PUBLISHED", "PENDING", "UNDER_REVIEW"])
                )
            listed_credits = float(self.db.execute(listing_stmt).scalar() or 0.0)
            
            owned_batches_data.append({
                "ownership_id": own.id,
                "batch_id": batch.id,
                "batch_number": batch.batch_number,
                "vintage_year": batch.vintage_year,
                "status": batch.status,
                "total_credits_owned": float(own.owned_credits),
                "available_credits": float(max(0.0, float(own.owned_credits) - listed_credits)),
                "listed_credits": listed_credits,
                "average_purchase_price": float(own.average_purchase_price) if own.average_purchase_price is not None else None,
                "project": {
                    "id": project.id if project else None,
                    "name": project.name if project else None,
                    "project_code": project.project_code if project else None,
                    "country": project.country if project else None
                } if project else None,
                "registry": {
                    "id": registry.id if registry else None,
                    "name": registry.name if registry else None
                } if registry else None
            })
            
        return owned_batches_data

    def get_available_credits(self, company_id: uuid.UUID) -> float:
        return self.ownership_service.calculate_available_credits(company_id)

    def calculate_portfolio_value(self, company_id: uuid.UUID) -> float:
        ownerships = self.ownership_service.get_company_ownerships(company_id)
        return float(sum(o.owned_credits * (o.average_purchase_price or 0.0) for o in ownerships))



class MarketplaceService(BaseService[MarketplaceListing]):
    def __init__(
        self,
        repository: MarketplaceRepository,
        ownership_repository: Optional[OwnershipRepository] = None,
        audit_service: Optional[AuditService] = None
    ) -> None:
        super().__init__(repository)
        self.ownership_repo = ownership_repository or OwnershipRepository(repository.db)
        from app.repositories.repositories import AuditRepository
        self.audit_service = audit_service or AuditService(AuditRepository(repository.db))

    def get_available_credits_for_ownership(self, ownership_id: uuid.UUID) -> float:
        own = self.ownership_repo.find_by_id(ownership_id)
        if not own:
            return 0.0
        from sqlalchemy import select, func
        listing_stmt = select(func.sum(MarketplaceListing.credits_for_sale))\
            .where(
                MarketplaceListing.ownership_id == ownership_id,
                MarketplaceListing.status.in_(["PUBLISHED", "PENDING", "UNDER_REVIEW"]),
                MarketplaceListing.deleted_at == None
            )
        listed_credits = float(self.repository.db.execute(listing_stmt).scalar() or 0.0)
        return float(max(0.0, float(own.owned_credits) - listed_credits))

    def validate_listing(self, data: dict, seller_company_id: uuid.UUID) -> None:
        ownership_id = uuid.UUID(str(data["ownership_id"]))
        own = self.ownership_repo.find_by_id(ownership_id)
        if not own:
            raise NotFoundException(f"Ownership record with ID {ownership_id} not found")
        if own.company_id != seller_company_id:
            raise PermissionDeniedException("You do not own this carbon credit ownership record")

        credits_for_sale = float(data["credits_for_sale"])
        price_per_credit = float(data["price_per_credit"])
        minimum_purchase = float(data.get("minimum_purchase", 1.0))

        if credits_for_sale <= 0:
            raise BusinessRuleException("Credits for sale must be greater than zero")
        if price_per_credit <= 0:
            raise BusinessRuleException("Price per credit must be greater than zero")
        if minimum_purchase < 1.0:
            raise BusinessRuleException("Minimum purchase must be at least 1 credit")
        if minimum_purchase > credits_for_sale:
            raise BusinessRuleException("Minimum purchase cannot exceed the total credits for sale")

        available = self.get_available_credits_for_ownership(ownership_id)
        if credits_for_sale > available:
            raise BusinessRuleException(f"Insufficient available credits. You have {available} available but requested to list {credits_for_sale}")

    def create_listing(self, seller_company_id: uuid.UUID, data: dict, user_id: uuid.UUID) -> MarketplaceListing:
        self.validate_listing(data, seller_company_id)
        
        listing_in = {
            "ownership_id": uuid.UUID(str(data["ownership_id"])),
            "seller_company_id": seller_company_id,
            "credits_for_sale": float(data["credits_for_sale"]),
            "price_per_credit": float(data["price_per_credit"]),
            "minimum_purchase": float(data.get("minimum_purchase", 1.0)),
            "description": data.get("description"),
            "status": ListingStatus.PENDING,
            "expires_at": data.get("expires_at")
        }
        
        listing = self.repository.create(listing_in)
        self.audit_service.record_event(
            user_id, seller_company_id, "MarketplaceListing", listing.id, "LISTING_CREATED",
            new_values={"credits_for_sale": listing.credits_for_sale, "price_per_credit": listing.price_per_credit}
        )
        return listing

    def update_listing(self, listing_id: uuid.UUID, data: dict, company_id: uuid.UUID, user_id: uuid.UUID) -> MarketplaceListing:
        listing = self.repository.find_by_id(listing_id)
        if not listing:
            raise NotFoundException(f"Marketplace listing with ID {listing_id} not found")
        if listing.seller_company_id != company_id:
            raise PermissionDeniedException("You are not authorized to update this listing")
            
        if listing.status in [ListingStatus.COMPLETED, ListingStatus.CANCELLED, ListingStatus.EXPIRED]:
            raise BusinessRuleException("Cannot update listing in terminal status")

        validate_data = {
            "ownership_id": data.get("ownership_id", listing.ownership_id),
            "credits_for_sale": data.get("credits_for_sale", listing.credits_for_sale),
            "price_per_credit": data.get("price_per_credit", listing.price_per_credit),
            "minimum_purchase": data.get("minimum_purchase", listing.minimum_purchase)
        }
        self.validate_listing(validate_data, company_id)

        old_vals = {"status": listing.status, "credits_for_sale": listing.credits_for_sale, "price": listing.price_per_credit}
        updated = self.repository.update(listing, data)
        new_vals = {"status": updated.status, "credits_for_sale": updated.credits_for_sale, "price": updated.price_per_credit}

        self.audit_service.record_event(
            user_id, company_id, "MarketplaceListing", updated.id, "LISTING_UPDATED",
            old_values=old_vals, new_values=new_vals
        )
        return updated

    def delete_listing(self, listing_id: uuid.UUID, company_id: uuid.UUID, user_id: uuid.UUID) -> None:
        listing = self.repository.find_by_id(listing_id)
        if not listing:
            raise NotFoundException(f"Marketplace listing with ID {listing_id} not found")
        if listing.seller_company_id != company_id:
            raise PermissionDeniedException("You are not authorized to delete this listing")
            
        listing.status = ListingStatus.CANCELLED
        self.repository.delete(listing)
        self.audit_service.record_event(
            user_id, company_id, "MarketplaceListing", listing_id, "LISTING_CANCELLED"
        )

    def approve_listing(self, listing_id: uuid.UUID, admin_id: uuid.UUID) -> MarketplaceListing:
        listing = self.repository.find_by_id(listing_id)
        if not listing:
            raise NotFoundException(f"Marketplace listing with ID {listing_id} not found")
            
        updated = self.repository.update(listing, {"status": ListingStatus.APPROVED})
        self.audit_service.record_event(
            admin_id, None, "MarketplaceListing", updated.id, "LISTING_APPROVED"
        )
        return updated

    def reject_listing(self, listing_id: uuid.UUID, admin_id: uuid.UUID) -> MarketplaceListing:
        listing = self.repository.find_by_id(listing_id)
        if not listing:
            raise NotFoundException(f"Marketplace listing with ID {listing_id} not found")
            
        updated = self.repository.update(listing, {"status": ListingStatus.REJECTED})
        self.audit_service.record_event(
            admin_id, None, "MarketplaceListing", updated.id, "LISTING_REJECTED"
        )
        return updated

    def publish_listing(self, listing_id: uuid.UUID, admin_id: uuid.UUID) -> MarketplaceListing:
        listing = self.repository.find_by_id(listing_id)
        if not listing:
            raise NotFoundException(f"Marketplace listing with ID {listing_id} not found")
            
        updated = self.repository.update(listing, {"status": ListingStatus.PUBLISHED})
        self.audit_service.record_event(
            admin_id, None, "MarketplaceListing", updated.id, "LISTING_PUBLISHED"
        )
        return updated

    def cancel_listing(self, listing_id: uuid.UUID, company_id: uuid.UUID, user_id: uuid.UUID) -> MarketplaceListing:
        listing = self.repository.find_by_id(listing_id)
        if not listing:
            raise NotFoundException(f"Marketplace listing with ID {listing_id} not found")
        if listing.seller_company_id != company_id:
            raise PermissionDeniedException("You are not authorized to cancel this listing")
            
        updated = self.repository.update(listing, {"status": ListingStatus.CANCELLED})
        self.audit_service.record_event(
            user_id, company_id, "MarketplaceListing", updated.id, "LISTING_CANCELLED"
        )
        return updated

    def expire_listing(self, listing_id: uuid.UUID) -> MarketplaceListing:
        listing = self.repository.find_by_id(listing_id)
        if not listing:
            raise NotFoundException(f"Marketplace listing with ID {listing_id} not found")
            
        updated = self.repository.update(listing, {"status": ListingStatus.EXPIRED})
        return updated

    def get_listing(self, listing_id: uuid.UUID) -> MarketplaceListing:
        listing = self.repository.find_by_id(listing_id)
        if not listing:
            raise NotFoundException(f"Marketplace listing with ID {listing_id} not found")
        return listing

    def list_listings(self) -> List[MarketplaceListing]:
        return self.repository.find_many()

    def search_marketplace(
        self,
        search_query: Optional[str] = None,
        registry_id: Optional[str] = None,
        country: Optional[str] = None,
        project_type: Optional[str] = None,
        vintage_year: Optional[int] = None,
        verification_standard: Optional[str] = None,
        status: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_credits: Optional[float] = None,
        skip: int = 0,
        limit: int = 100,
        sort_field: Optional[str] = None,
        sort_order: str = "asc"
    ) -> Tuple[List[MarketplaceListing], int]:
        return self.repository.search(
            search_query=search_query,
            registry_id=registry_id,
            country=country,
            project_type=project_type,
            vintage_year=vintage_year,
            verification_standard=verification_standard,
            status=status,
            min_price=min_price,
            max_price=max_price,
            min_credits=min_credits,
            skip=skip,
            limit=limit,
            sort_field=sort_field,
            sort_order=sort_order
        )


class OrderService(BaseService[PurchaseOrder]):
    def __init__(
        self,
        repository: OrderRepository,
        marketplace_service: Optional[MarketplaceService] = None,
        ownership_service: Optional[OwnershipService] = None,
        audit_service: Optional[AuditService] = None
    ) -> None:
        super().__init__(repository)
        self.marketplace_service = marketplace_service or MarketplaceService(MarketplaceRepository(repository.db))
        from app.repositories.repositories import OwnershipRepository, AuditRepository
        self.ownership_service = ownership_service or OwnershipService(OwnershipRepository(repository.db))
        self.audit_service = audit_service or AuditService(AuditRepository(repository.db))

    def validate_order(self, buyer_company_id: uuid.UUID, listing: MarketplaceListing, requested_credits: float) -> None:
        if listing.status != ListingStatus.PUBLISHED:
            raise BusinessRuleException("Listing is not available for purchase (must be in PUBLISHED status)")
        if listing.expires_at and listing.expires_at.tzinfo is None:
            expires_at = listing.expires_at.replace(tzinfo=timezone.utc)
        else:
            expires_at = listing.expires_at
            
        if expires_at and expires_at < datetime.now(timezone.utc):
            raise BusinessRuleException("Listing has expired and cannot be purchased")
            
        if listing.seller_company_id == buyer_company_id:
            raise BusinessRuleException("Self-purchase attempt: Buyer cannot purchase credits from their own listing")
            
        if requested_credits <= 0:
            raise BusinessRuleException("Requested credits must be greater than zero")
            
        if requested_credits > float(listing.credits_for_sale):
            raise BusinessRuleException(f"Insufficient credits for sale. Requested {requested_credits} but only {listing.credits_for_sale} are available")
            
        if requested_credits < float(listing.minimum_purchase):
            raise BusinessRuleException(f"Requested credits {requested_credits} is below the listing's minimum purchase limit of {listing.minimum_purchase}")

    def create_order(self, buyer_company_id: uuid.UUID, data: dict, user_id: uuid.UUID) -> PurchaseOrder:
        listing_id = uuid.UUID(str(data["listing_id"]))
        requested_credits = float(data["requested_credits"])

        listing = self.marketplace_service.get_listing(listing_id)
        self.validate_order(buyer_company_id, listing, requested_credits)

        db = self.repository.db
        
        seller_ownership = db.query(Ownership).filter(Ownership.id == listing.ownership_id).first()
        if not seller_ownership or float(seller_ownership.owned_credits) < requested_credits:
            order = PurchaseOrder(
                id=uuid.uuid4(),
                listing_id=listing.id,
                buyer_company_id=buyer_company_id,
                requested_credits=requested_credits,
                price_per_credit=float(listing.price_per_credit),
                total_price=float(requested_credits * float(listing.price_per_credit)),
                status=PurchaseOrderStatus.FAILED
            )
            db.add(order)
            db.commit()
            raise BusinessRuleException("Seller has insufficient owned credits to fulfill this request")

        try:
            order = PurchaseOrder(
                id=uuid.uuid4(),
                listing_id=listing.id,
                buyer_company_id=buyer_company_id,
                requested_credits=requested_credits,
                price_per_credit=float(listing.price_per_credit),
                total_price=float(requested_credits * float(listing.price_per_credit)),
                status=PurchaseOrderStatus.COMPLETED
            )
            db.add(order)

            seller_ownership.owned_credits = float(float(seller_ownership.owned_credits) - requested_credits)

            batch_id = seller_ownership.batch_id
            buyer_ownership = db.query(Ownership).filter(
                Ownership.company_id == buyer_company_id,
                Ownership.batch_id == batch_id
            ).first()

            if buyer_ownership:
                curr_credits = float(buyer_ownership.owned_credits)
                curr_avg = float(buyer_ownership.average_purchase_price or 0.0)
                
                buyer_ownership.owned_credits = float(curr_credits + requested_credits)
                if (curr_credits + requested_credits) > 0:
                    new_avg = ((curr_credits * curr_avg) + (requested_credits * float(listing.price_per_credit))) / (curr_credits + requested_credits)
                    buyer_ownership.average_purchase_price = float(new_avg)
            else:
                buyer_ownership = Ownership(
                    id=uuid.uuid4(),
                    company_id=buyer_company_id,
                    batch_id=batch_id,
                    owned_credits=requested_credits,
                    average_purchase_price=float(listing.price_per_credit)
                )
                db.add(buyer_ownership)
                db.flush()

            listing.credits_for_sale = float(float(listing.credits_for_sale) - requested_credits)
            if listing.credits_for_sale <= 0.0001:
                listing.status = ListingStatus.COMPLETED

            tx = Transaction(
                id=uuid.uuid4(),
                order_id=order.id,
                buyer_company_id=buyer_company_id,
                seller_company_id=listing.seller_company_id,
                ownership_id=buyer_ownership.id,
                credits_transferred=requested_credits,
                price_per_credit=float(listing.price_per_credit),
                total_price=float(requested_credits * float(listing.price_per_credit)),
                status="COMPLETED",
                completed_at=datetime.now(timezone.utc)
            )
            db.add(tx)

            self.audit_service.record_event(
                user_id, buyer_company_id, "PurchaseOrder", order.id, "Order Created",
                new_values={"total_price": float(order.total_price)}
            )
            self.audit_service.record_event(
                user_id, buyer_company_id, "PurchaseOrder", order.id, "Order Completed",
                new_values={"total_price": float(order.total_price)}
            )
            self.audit_service.record_event(
                user_id, buyer_company_id, "Transaction", tx.id, "Transaction Completed",
                new_values={"credits": requested_credits, "price": float(tx.price_per_credit)}
            )
            self.audit_service.record_event(
                user_id, buyer_company_id, "Ownership", buyer_ownership.id, "Ownership Updated",
                new_values={"new_credits": float(buyer_ownership.owned_credits)}
            )

            db.commit()
            
            # Trigger on-chain registry of transaction
            from app.blockchain.service import BlockchainService
            b_service = BlockchainService()
            b_service.submit_to_blockchain("Transaction", tx.id)
        except Exception as exc:
            db.rollback()
            try:
                order.status = PurchaseOrderStatus.FAILED
                db.commit()
            except Exception:
                db.rollback()
            raise exc

        return order

    def cancel_order(self, order_id: uuid.UUID, company_id: uuid.UUID, user_id: uuid.UUID) -> PurchaseOrder:
        order = self.repository.find_by_id(order_id)
        if not order:
            raise NotFoundException(f"Purchase order with ID {order_id} not found")
        if order.buyer_company_id != company_id:
            raise PermissionDeniedException("You are not authorized to cancel this order")
        if order.status not in [PurchaseOrderStatus.PENDING, PurchaseOrderStatus.PROCESSING]:
            raise BusinessRuleException("Only pending or processing orders can be cancelled")
            
        updated = self.repository.update(order, {"status": PurchaseOrderStatus.CANCELLED})
        self.audit_service.record_event(
            user_id, company_id, "PurchaseOrder", updated.id, "ORDER_CANCELLED"
        )
        return updated

    def get_order(self, order_id: uuid.UUID) -> PurchaseOrder:
        order = self.repository.find_by_id(order_id)
        if not order:
            raise NotFoundException(f"Purchase order with ID {order_id} not found")
        return order

    def list_orders(self, buyer_company_id: Optional[uuid.UUID] = None) -> List[PurchaseOrder]:
        if buyer_company_id:
            return self.repository.find_by_buyer_company(buyer_company_id)
        return self.repository.find_many()


class TransactionService(BaseService[Transaction]):
    def __init__(self, repository: TransactionRepository) -> None:
        super().__init__(repository)

    def get_transaction(self, transaction_id: uuid.UUID) -> Transaction:
        tx = self.repository.find_by_id(transaction_id)
        if not tx:
            raise NotFoundException(f"Transaction with ID {transaction_id} not found")
        return tx

    def list_transactions(self, company_id: Optional[uuid.UUID] = None) -> List[Transaction]:
        if company_id:
            return self.repository.find_by_company(company_id)
        return self.repository.find_many()

    def search_transactions(self, search_query: Optional[str] = None) -> List[Transaction]:
        from sqlalchemy import select, or_
        from app.models.models import Company
        stmt = select(Transaction)
        if search_query:
            stmt = stmt.outerjoin(Company, or_(Company.id == Transaction.buyer_company_id, Company.id == Transaction.seller_company_id))\
                .where(Company.name.ilike(f"%{search_query}%"))
        return list(self.repository.db.execute(stmt).scalars().all())


class RetirementService(BaseService[Retirement]):
    def __init__(self, repository: RetirementRepository, audit_service: Optional[AuditService] = None) -> None:
        super().__init__(repository)
        self.audit_service = audit_service or AuditService(AuditRepository(repository.db))

    def retire_credits(
        self,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        ownership_id: uuid.UUID,
        quantity: float,
        beneficiary_name: str,
        reason: str
    ) -> Retirement:
        db = self.repository.db
        
        # 1. Perform validations first to keep transaction safety
        ownership = db.query(Ownership).filter(Ownership.id == ownership_id).first()
        if not ownership:
            raise NotFoundException(f"Ownership record with ID {ownership_id} not found")
        if ownership.company_id != company_id:
            raise PermissionDeniedException("You are not authorized to retire credits from this ownership")
        if float(ownership.owned_credits) < quantity:
            raise BusinessRuleException(
                f"Insufficient credits. You only own {ownership.owned_credits} but requested to retire {quantity}"
            )

        # Generate unique certificate number
        batch = ownership.batch
        vintage_year = batch.vintage_year if batch else "0000"
        cert_number = f"CL-CERT-{uuid.uuid4().hex[:8].upper()}-{vintage_year}"

        try:
            # 2. Modify ownership and insert retirement record
            ownership.owned_credits = float(float(ownership.owned_credits) - quantity)

            retirement = Retirement(
                id=uuid.uuid4(),
                ownership_id=ownership_id,
                company_id=company_id,
                credits_retired=quantity,
                reason=reason,
                certificate_number=cert_number,
                blockchain_tx_hash=None
            )
            db.add(retirement)

            # Record event via audit service
            self.audit_service.record_event(
                user_id=user_id,
                company_id=company_id,
                entity_type="Retirement",
                entity_id=retirement.id,
                action="Credits Retired",
                new_values={
                    "quantity": quantity,
                    "certificate_number": cert_number,
                    "batch_number": batch.batch_number if batch else None
                }
            )

            db.commit()

            # Trigger on-chain registry of retirement
            from app.blockchain.service import BlockchainService
            b_service = BlockchainService()
            b_service.submit_to_blockchain("Retirement", retirement.id)

            return retirement
        except Exception as exc:
            db.rollback()
            raise exc

    def validate_retirement(self, ownership_id: uuid.UUID, quantity: float) -> bool:
        ownership = self.repository.db.query(Ownership).filter(Ownership.id == ownership_id).first()
        if not ownership:
            return False
        return float(ownership.owned_credits) >= quantity

    def get_retirement(self, retirement_id: uuid.UUID) -> Retirement:
        ret = self.repository.find_by_id(retirement_id)
        if not ret:
            raise NotFoundException(f"Retirement with ID {retirement_id} not found")
        return ret

    def list_retirements(self, company_id: Optional[uuid.UUID] = None) -> List[Retirement]:
        if company_id:
            return self.repository.find_by_company(company_id)
        return self.repository.find_many()

    def generate_certificate(self, retirement_id: uuid.UUID) -> dict:
        ret = self.get_retirement(retirement_id)
        ownership = ret.ownership
        batch = ownership.batch if ownership else None
        project = batch.project if batch else None
        registry = project.registry if project else None
        
        return {
            "certificate_number": ret.certificate_number,
            "company": {
                "id": str(ret.company.id),
                "name": ret.company.name
            },
            "project": {
                "id": str(project.id) if project else None,
                "name": project.name if project else None,
                "project_code": project.project_code if project else None
            } if project else None,
            "registry": {
                "id": str(registry.id) if registry else None,
                "name": registry.name if registry else None
            } if registry else None,
            "batch_number": batch.batch_number if batch else None,
            "credits_retired": float(ret.credits_retired),
            "reason": ret.reason,
            "retirement_date": ret.retired_at.isoformat(),
            "verification_status": "VERIFIED",
            "blockchain_hash": ret.blockchain_tx_hash
        }

    def verify_retirement(self, certificate_number: str) -> dict:
        ret = self.repository.find_by_certificate(certificate_number)
        if not ret:
            raise NotFoundException(f"Retirement certificate {certificate_number} not found")
        return self.generate_certificate(ret.id)


class AnalyticsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_dashboard(self, company_id: Optional[uuid.UUID] = None) -> dict:
        from sqlalchemy import select, func
        from app.models.models import Company, Registry, CarbonProject, CreditBatch, Transaction, Retirement, Ownership
        
        # Global Counts
        total_companies = self.db.execute(select(func.count(Company.id))).scalar() or 0
        total_registries = self.db.execute(select(func.count(Registry.id))).scalar() or 0
        total_projects = self.db.execute(select(func.count(CarbonProject.id))).scalar() or 0
        total_batches = self.db.execute(select(func.count(CreditBatch.id))).scalar() or 0
        
        # Volume
        volume_stmt = select(func.sum(Transaction.total_price)).where(Transaction.status == "COMPLETED")
        if company_id:
            from sqlalchemy import or_
            volume_stmt = volume_stmt.where(or_(
                Transaction.buyer_company_id == company_id,
                Transaction.seller_company_id == company_id
            ))
        marketplace_volume = float(self.db.execute(volume_stmt).scalar() or 0.0)
        
        # Completed Transactions
        tx_count_stmt = select(func.count(Transaction.id)).where(Transaction.status == "COMPLETED")
        if company_id:
            from sqlalchemy import or_
            tx_count_stmt = tx_count_stmt.where(or_(
                Transaction.buyer_company_id == company_id,
                Transaction.seller_company_id == company_id
            ))
        completed_transactions = self.db.execute(tx_count_stmt).scalar() or 0
        
        # Credits Retired
        retired_stmt = select(func.sum(Retirement.credits_retired))
        if company_id:
            retired_stmt = retired_stmt.where(Retirement.company_id == company_id)
        credits_retired = float(self.db.execute(retired_stmt).scalar() or 0.0)
        
        # Credits Available
        avail_stmt = select(func.sum(Ownership.owned_credits))
        if company_id:
            avail_stmt = avail_stmt.where(Ownership.company_id == company_id)
        credits_available = float(self.db.execute(avail_stmt).scalar() or 0.0)
        
        return {
            "total_companies": total_companies,
            "total_registries": total_registries,
            "total_projects": total_projects,
            "total_credit_batches": total_batches,
            "marketplace_volume": marketplace_volume,
            "completed_transactions": completed_transactions,
            "credits_retired": credits_retired,
            "credits_available": credits_available
        }

    def get_portfolio_statistics(self, company_id: uuid.UUID) -> dict:
        from sqlalchemy import select, func
        from app.models.models import Ownership, MarketplaceListing, Retirement, ListingStatus
        
        # Credits Owned
        owned_stmt = select(func.sum(Ownership.owned_credits)).where(Ownership.company_id == company_id)
        credits_owned = float(self.db.execute(owned_stmt).scalar() or 0.0)
        
        # Credits Listed
        listed_stmt = select(func.sum(MarketplaceListing.credits_for_sale))\
            .join(Ownership, Ownership.id == MarketplaceListing.ownership_id)\
            .where(Ownership.company_id == company_id)\
            .where(MarketplaceListing.status == ListingStatus.PUBLISHED)
        credits_listed = float(self.db.execute(listed_stmt).scalar() or 0.0)
        
        # Credits Retired
        retired_stmt = select(func.sum(Retirement.credits_retired)).where(Retirement.company_id == company_id)
        credits_retired = float(self.db.execute(retired_stmt).scalar() or 0.0)
        
        # Estimated Portfolio Value
        val_stmt = select(func.sum(Ownership.owned_credits * Ownership.average_purchase_price)).where(Ownership.company_id == company_id)
        estimated_value = float(self.db.execute(val_stmt).scalar() or 0.0)
        
        return {
            "credits_owned": credits_owned,
            "credits_listed": credits_listed,
            "credits_retired": credits_retired,
            "estimated_portfolio_value": estimated_value
        }

    def get_marketplace_statistics(self) -> dict:
        from sqlalchemy import select, func
        from app.models.models import MarketplaceListing, PurchaseOrder, Transaction, ListingStatus, PurchaseOrderStatus, Registry, CarbonProject, CreditBatch, Ownership
        
        active_listings = self.db.execute(select(func.count(MarketplaceListing.id)).where(MarketplaceListing.status == ListingStatus.PUBLISHED)).scalar() or 0
        pending_listings = self.db.execute(select(func.count(MarketplaceListing.id)).where(MarketplaceListing.status == ListingStatus.PENDING)).scalar() or 0
        completed_orders = self.db.execute(select(func.count(PurchaseOrder.id)).where(PurchaseOrder.status == PurchaseOrderStatus.COMPLETED)).scalar() or 0
        
        avg_price = float(self.db.execute(select(func.avg(Transaction.price_per_credit)).where(Transaction.status == "COMPLETED")).scalar() or 0.0)
        
        # Most Active Registry
        reg_stmt = select(Registry.name)\
            .join(CarbonProject, CarbonProject.registry_id == Registry.id)\
            .join(CreditBatch, CreditBatch.project_id == CarbonProject.id)\
            .join(Ownership, Ownership.batch_id == CreditBatch.id)\
            .join(Transaction, Transaction.ownership_id == Ownership.id)\
            .where(Transaction.status == "COMPLETED")\
            .group_by(Registry.name)\
            .order_by(func.sum(Transaction.credits_transferred).desc())\
            .limit(1)
        most_active_registry = self.db.execute(reg_stmt).scalar() or "N/A"
        
        # Most Active Project
        proj_stmt = select(CarbonProject.name)\
            .join(CreditBatch, CreditBatch.project_id == CarbonProject.id)\
            .join(Ownership, Ownership.batch_id == CreditBatch.id)\
            .join(Transaction, Transaction.ownership_id == Ownership.id)\
            .where(Transaction.status == "COMPLETED")\
            .group_by(CarbonProject.name)\
            .order_by(func.sum(Transaction.credits_transferred).desc())\
            .limit(1)
        most_active_project = self.db.execute(proj_stmt).scalar() or "N/A"
        
        return {
            "active_listings": active_listings,
            "pending_listings": pending_listings,
            "completed_orders": completed_orders,
            "average_price": avg_price,
            "most_active_registry": most_active_registry,
            "most_active_project": most_active_project
        }

    def get_retirement_statistics(self, company_id: Optional[uuid.UUID] = None) -> dict:
        from sqlalchemy import select, func
        from app.models.models import Retirement
        stmt_sum = select(func.sum(Retirement.credits_retired))
        stmt_count = select(func.count(Retirement.id))
        
        if company_id:
            stmt_sum = stmt_sum.where(Retirement.company_id == company_id)
            stmt_count = stmt_count.where(Retirement.company_id == company_id)
            
        total_retired = float(self.db.execute(stmt_sum).scalar() or 0.0)
        total_retirements = self.db.execute(stmt_count).scalar() or 0
        
        return {
            "total_credits_retired": total_retired,
            "total_retirements": total_retirements
        }

    def get_registry_statistics(self) -> dict:
        from sqlalchemy import select, func
        from app.models.models import Registry, CarbonProject, CreditBatch
        
        # Number of projects per registry
        stmt = select(Registry.name, func.count(CarbonProject.id))\
            .join(CarbonProject, CarbonProject.registry_id == Registry.id)\
            .group_by(Registry.name)
        project_distribution = {row[0]: row[1] for row in self.db.execute(stmt).all()}
        
        # Credits issued per registry
        stmt_credits = select(Registry.name, func.sum(CreditBatch.total_credits))\
            .join(CarbonProject, CarbonProject.registry_id == Registry.id)\
            .join(CreditBatch, CreditBatch.project_id == CarbonProject.id)\
            .group_by(Registry.name)
        credit_distribution = {row[0]: float(row[1] or 0.0) for row in self.db.execute(stmt_credits).all()}
        
        return {
            "project_distribution": project_distribution,
            "credit_distribution": credit_distribution
        }


class AdminService:
    def __init__(self, db: Session, audit_service: Optional[AuditService] = None) -> None:
        self.db = db
        self.audit_service = audit_service or AuditService(AuditRepository(db))

    def get_dashboard(self) -> dict:
        from sqlalchemy import select, func
        from app.models.models import User, Company, Registry, CarbonProject, CreditBatch, MarketplaceListing, PurchaseOrder, Transaction, Retirement
        
        users_count = self.db.execute(select(func.count(User.id))).scalar() or 0
        companies_count = self.db.execute(select(func.count(Company.id))).scalar() or 0
        registries_count = self.db.execute(select(func.count(Registry.id))).scalar() or 0
        projects_count = self.db.execute(select(func.count(CarbonProject.id))).scalar() or 0
        batches_count = self.db.execute(select(func.count(CreditBatch.id))).scalar() or 0
        listings_count = self.db.execute(select(func.count(MarketplaceListing.id))).scalar() or 0
        orders_count = self.db.execute(select(func.count(PurchaseOrder.id))).scalar() or 0
        txs_count = self.db.execute(select(func.count(Transaction.id))).scalar() or 0
        retirements_count = self.db.execute(select(func.count(Retirement.id))).scalar() or 0
        
        return {
            "users_count": users_count,
            "companies_count": companies_count,
            "registries_count": registries_count,
            "projects_count": projects_count,
            "batches_count": batches_count,
            "listings_count": listings_count,
            "orders_count": orders_count,
            "transactions_count": txs_count,
            "retirements_count": retirements_count
        }

    def list_users(self, search: Optional[str] = None, skip: int = 0, limit: int = 100) -> tuple[List[User], int]:
        from sqlalchemy import select, or_, func
        stmt = select(User)
        if search:
            stmt = stmt.where(or_(
                User.first_name.ilike(f"%{search}%"),
                User.last_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            ))
        total = self.db.execute(select(func.count()).select_from(stmt.subquery())).scalar() or 0
        items = list(self.db.execute(stmt.offset(skip).limit(limit)).scalars().all())
        return items, total

    def list_companies(self, search: Optional[str] = None, skip: int = 0, limit: int = 100) -> tuple[List[Company], int]:
        from sqlalchemy import select, or_, func
        stmt = select(Company)
        if search:
            stmt = stmt.where(or_(
                Company.name.ilike(f"%{search}%"),
                Company.registration_number.ilike(f"%{search}%"),
                Company.country.ilike(f"%{search}%")
            ))
        total = self.db.execute(select(func.count()).select_from(stmt.subquery())).scalar() or 0
        items = list(self.db.execute(stmt.offset(skip).limit(limit)).scalars().all())
        return items, total

    def list_registries(self, search: Optional[str] = None, skip: int = 0, limit: int = 100) -> tuple[List[Registry], int]:
        from sqlalchemy import select, or_, func
        stmt = select(Registry)
        if search:
            stmt = stmt.where(or_(
                Registry.name.ilike(f"%{search}%"),
                Registry.country.ilike(f"%{search}%"),
                Registry.website.ilike(f"%{search}%")
            ))
        total = self.db.execute(select(func.count()).select_from(stmt.subquery())).scalar() or 0
        items = list(self.db.execute(stmt.offset(skip).limit(limit)).scalars().all())
        return items, total

    def list_projects(self, search: Optional[str] = None, skip: int = 0, limit: int = 100) -> tuple[List[CarbonProject], int]:
        from sqlalchemy import select, or_, func
        stmt = select(CarbonProject)
        if search:
            stmt = stmt.where(or_(
                CarbonProject.name.ilike(f"%{search}%"),
                CarbonProject.project_code.ilike(f"%{search}%"),
                CarbonProject.country.ilike(f"%{search}%")
            ))
        total = self.db.execute(select(func.count()).select_from(stmt.subquery())).scalar() or 0
        items = list(self.db.execute(stmt.offset(skip).limit(limit)).scalars().all())
        return items, total

    def list_batches(self, search: Optional[str] = None, skip: int = 0, limit: int = 100) -> tuple[List[CreditBatch], int]:
        from sqlalchemy import select, or_, func
        stmt = select(CreditBatch)
        if search:
            stmt = stmt.where(CreditBatch.batch_number.ilike(f"%{search}%"))
        total = self.db.execute(select(func.count()).select_from(stmt.subquery())).scalar() or 0
        items = list(self.db.execute(stmt.offset(skip).limit(limit)).scalars().all())
        return items, total

    def list_listings(self, search: Optional[str] = None, skip: int = 0, limit: int = 100) -> tuple[List[MarketplaceListing], int]:
        from sqlalchemy import select, or_, func
        from app.models.models import Company
        stmt = select(MarketplaceListing).outerjoin(Company, Company.id == MarketplaceListing.seller_company_id)
        if search:
            stmt = stmt.where(or_(
                MarketplaceListing.description.ilike(f"%{search}%"),
                Company.name.ilike(f"%{search}%")
            ))
        total = self.db.execute(select(func.count()).select_from(stmt.subquery())).scalar() or 0
        items = list(self.db.execute(stmt.offset(skip).limit(limit)).scalars().all())
        return items, total

    def list_orders(self, search: Optional[str] = None, skip: int = 0, limit: int = 100) -> tuple[List[PurchaseOrder], int]:
        from sqlalchemy import select, or_, func
        from app.models.models import Company
        stmt = select(PurchaseOrder).outerjoin(Company, Company.id == PurchaseOrder.buyer_company_id)
        if search:
            stmt = stmt.where(or_(
                Company.name.ilike(f"%{search}%"),
                PurchaseOrder.payment_reference.ilike(f"%{search}%")
            ))
        total = self.db.execute(select(func.count()).select_from(stmt.subquery())).scalar() or 0
        items = list(self.db.execute(stmt.offset(skip).limit(limit)).scalars().all())
        return items, total

    def list_transactions(self, search: Optional[str] = None, skip: int = 0, limit: int = 100) -> tuple[List[Transaction], int]:
        from sqlalchemy import select, or_, func
        from app.models.models import Company
        stmt = select(Transaction).outerjoin(Company, or_(Company.id == Transaction.buyer_company_id, Company.id == Transaction.seller_company_id))
        if search:
            stmt = stmt.where(Company.name.ilike(f"%{search}%"))
        total = self.db.execute(select(func.count()).select_from(stmt.subquery())).scalar() or 0
        items = list(self.db.execute(stmt.offset(skip).limit(limit)).scalars().all())
        return items, total

    def list_retirements(self, search: Optional[str] = None, skip: int = 0, limit: int = 100) -> tuple[List[Retirement], int]:
        from sqlalchemy import select, or_, func
        from app.models.models import Company
        stmt = select(Retirement).outerjoin(Company, Company.id == Retirement.company_id)
        if search:
            stmt = stmt.where(or_(
                Retirement.certificate_number.ilike(f"%{search}%"),
                Retirement.reason.ilike(f"%{search}%"),
                Company.name.ilike(f"%{search}%")
            ))
        total = self.db.execute(select(func.count()).select_from(stmt.subquery())).scalar() or 0
        items = list(self.db.execute(stmt.offset(skip).limit(limit)).scalars().all())
        return items, total

    def activate_company(self, company_id: uuid.UUID, admin_user_id: uuid.UUID) -> Company:
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise NotFoundException(f"Company with ID {company_id} not found")
        company.is_active = True
        company.status = CompanyStatus.ACTIVE
        self.db.commit()
        self.audit_service.record_event(
            user_id=admin_user_id,
            company_id=None,
            entity_type="Company",
            entity_id=company_id,
            action="Company Activated",
            new_values={"status": "ACTIVE", "is_active": True}
        )
        return company

    def deactivate_company(self, company_id: uuid.UUID, admin_user_id: uuid.UUID) -> Company:
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise NotFoundException(f"Company with ID {company_id} not found")
        company.is_active = False
        company.status = CompanyStatus.SUSPENDED
        self.db.commit()
        self.audit_service.record_event(
            user_id=admin_user_id,
            company_id=None,
            entity_type="Company",
            entity_id=company_id,
            action="Company Deactivated",
            new_values={"status": "SUSPENDED", "is_active": False}
        )
        return company

    def activate_user(self, user_id: uuid.UUID, admin_user_id: uuid.UUID) -> User:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundException(f"User with ID {user_id} not found")
        user.is_active = True
        self.db.commit()
        self.audit_service.record_event(
            user_id=admin_user_id,
            company_id=None,
            entity_type="User",
            entity_id=user_id,
            action="User Activated",
            new_values={"is_active": True}
        )
        return user

    def deactivate_user(self, user_id: uuid.UUID, admin_user_id: uuid.UUID) -> User:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundException(f"User with ID {user_id} not found")
        user.is_active = False
        self.db.commit()
        self.audit_service.record_event(
            user_id=admin_user_id,
            company_id=None,
            entity_type="User",
            entity_id=user_id,
            action="User Deactivated",
            new_values={"is_active": False}
        )
        return user
