import enum
import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    UUID,
    JSON,
    TypeDecorator,
    text
)
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class JSONB(TypeDecorator):
    """
    Database-agnostic JSONB type.
    Uses PostgreSQL's native JSONB type, and falls back to standard JSON on SQLite.
    """
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_JSONB())
        return dialect.type_descriptor(JSON())


# ==============================================================================
# ENUM DEFINITIONS
# ==============================================================================

class CompanyStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    COMPANY_ADMIN = "COMPANY_ADMIN"
    TRADER = "TRADER"
    AUDITOR = "AUDITOR"
    VIEWER = "VIEWER"


class DocumentType(str, enum.Enum):
    VERIFICATION_CERTIFICATE = "Verification Certificate"
    MONITORING_REPORT = "Monitoring Report"
    METHODOLOGY = "Methodology"
    ISSUANCE_CERTIFICATE = "Issuance Certificate"
    IMAGE = "Image"
    OTHER = "Other"


class BatchStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PARTIALLY_USED = "PARTIALLY_USED"
    RETIRED = "RETIRED"
    EXPIRED = "EXPIRED"


class ListingStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"


class PurchaseOrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


# ==============================================================================
# MODEL MIXINS
# ==============================================================================

class PrimaryKeyMixin:
    """Mixin to inject UUID primary key."""
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )


class TimestampMixin:
    """Mixin to inject standard audit timestamps."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class SoftDeleteMixin:
    """Mixin to inject soft delete timestamp."""
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )


# ==============================================================================
# DATABASE MODELS
# ==============================================================================

class Company(Base, PrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    registration_number: Mapped[str] = mapped_column(String(100), nullable=False)
    industry: Mapped[str] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    wallet_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email_domain: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[CompanyStatus] = mapped_column(
        Enum(CompanyStatus, name="company_status_enum"),
        nullable=False,
        default=CompanyStatus.ACTIVE,
    )

    # Relationships
    users: Mapped[List["User"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    ownerships: Mapped[List["Ownership"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    listings: Mapped[List["MarketplaceListing"]] = relationship(back_populates="seller_company", cascade="all, delete-orphan")
    purchase_orders: Mapped[List["PurchaseOrder"]] = relationship(back_populates="buyer_company", cascade="all, delete-orphan")
    sent_transactions: Mapped[List["Transaction"]] = relationship(
        foreign_keys="[Transaction.seller_company_id]", back_populates="seller_company"
    )
    received_transactions: Mapped[List["Transaction"]] = relationship(
        foreign_keys="[Transaction.buyer_company_id]", back_populates="buyer_company"
    )
    retirements: Mapped[List["Retirement"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    audit_logs: Mapped[List["AuditLog"]] = relationship(back_populates="company")

    # Table constraints and indexes
    __table_args__ = (
        UniqueConstraint("name", name="uq_companies_name"),
        UniqueConstraint("registration_number", name="uq_companies_registration_number"),
        UniqueConstraint("wallet_address", name="uq_companies_wallet_address"),
        Index("idx_companies_name", "name"),
        Index("idx_companies_registration_number", "registration_number"),
        Index("idx_companies_wallet_address", "wallet_address"),
        Index("idx_companies_status", "status"),
    )


class User(Base, PrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("companies.id", ondelete="SET NULL"),
        nullable=True,
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role_enum"),
        nullable=False,
        default=UserRole.VIEWER,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    company: Mapped[Optional["Company"]] = relationship(back_populates="users")
    audit_logs: Mapped[List["AuditLog"]] = relationship(back_populates="user")
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        Index("idx_users_email", "email"),
        Index("idx_users_role", "role"),
        Index("idx_users_is_active", "is_active"),
    )


class Registry(Base, PrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "registries"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    website: Mapped[str] = mapped_column(String(255), nullable=False)
    accreditation: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ACTIVE")

    # Relationships
    projects: Mapped[List["CarbonProject"]] = relationship(back_populates="registry", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("name", name="uq_registries_name"),
        Index("idx_registries_name", "name"),
        Index("idx_registries_status", "status"),
    )


class CarbonProject(Base, PrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "carbon_projects"

    registry_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("registries.id", ondelete="RESTRICT"),
        nullable=False,
    )
    project_code: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    project_type: Mapped[str] = mapped_column(String(100), nullable=False)
    verification_standard: Mapped[str] = mapped_column(String(100), nullable=False)
    methodology: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    developer: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")

    # Relationships
    registry: Mapped["Registry"] = relationship(back_populates="projects")
    documents: Mapped[List["ProjectDocument"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    batches: Mapped[List["CreditBatch"]] = relationship(back_populates="project", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("project_code", name="uq_carbon_projects_project_code"),
        Index("idx_carbon_projects_project_code", "project_code"),
        Index("idx_carbon_projects_name", "name"),
        Index("idx_carbon_projects_status", "status"),
    )


class ProjectDocument(Base, PrimaryKeyMixin, TimestampMixin):
    __tablename__ = "project_documents"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("carbon_projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, name="document_type_enum"),
        nullable=False,
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
    )

    # Relationships
    project: Mapped["CarbonProject"] = relationship(back_populates="documents")


class CreditBatch(Base, PrimaryKeyMixin, TimestampMixin):
    __tablename__ = "credit_batches"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("carbon_projects.id", ondelete="RESTRICT"),
        nullable=False,
    )
    batch_number: Mapped[str] = mapped_column(String(100), nullable=False)
    vintage_year: Mapped[int] = mapped_column(Integer, nullable=False)
    total_credits: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    remaining_credits: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    issuance_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[BatchStatus] = mapped_column(
        Enum(BatchStatus, name="batch_status_enum"),
        nullable=False,
        default=BatchStatus.ACTIVE,
    )
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    blockchain_status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")
    blockchain_tx_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    block_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    blockchain_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    project: Mapped["CarbonProject"] = relationship(back_populates="batches")
    ownerships: Mapped[List["Ownership"]] = relationship(back_populates="batch", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("batch_number", name="uq_credit_batches_batch_number"),
        CheckConstraint("total_credits > 0", name="chk_credit_batches_total_credits_positive"),
        CheckConstraint("remaining_credits >= 0", name="chk_credit_batches_remaining_credits_nonnegative"),
        CheckConstraint("remaining_credits <= total_credits", name="chk_credit_batches_remaining_credits_limit"),
        CheckConstraint(f"vintage_year <= {datetime.now(timezone.utc).year}", name="chk_credit_batches_vintage_year_limit"),
        Index("idx_credit_batches_batch_number", "batch_number"),
        Index("idx_credit_batches_vintage_year", "vintage_year"),
        Index("idx_credit_batches_status", "status"),
    )


class Ownership(Base, PrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ownerships"

    batch_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("credit_batches.id", ondelete="RESTRICT"),
        nullable=False,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"),
        nullable=False,
    )
    owned_credits: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    average_purchase_price: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)

    # Relationships
    batch: Mapped["CreditBatch"] = relationship(back_populates="ownerships")
    company: Mapped["Company"] = relationship(back_populates="ownerships")
    listings: Mapped[List["MarketplaceListing"]] = relationship(back_populates="ownership", cascade="all, delete-orphan")
    retirements: Mapped[List["Retirement"]] = relationship(back_populates="ownership", cascade="all, delete-orphan")
    transactions: Mapped[List["Transaction"]] = relationship(back_populates="ownership")

    __table_args__ = (
        CheckConstraint("owned_credits > 0", name="chk_ownerships_owned_credits_positive"),
        CheckConstraint("average_purchase_price >= 0", name="chk_ownerships_average_purchase_price_nonnegative"),
        Index("idx_ownerships_batch_company", "batch_id", "company_id"),
    )


class MarketplaceListing(Base, PrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "marketplace_listings"

    ownership_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ownerships.id", ondelete="RESTRICT"),
        nullable=False,
    )
    seller_company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"),
        nullable=False,
    )
    credits_for_sale: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    price_per_credit: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    minimum_purchase: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=1.0)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[ListingStatus] = mapped_column(
        Enum(ListingStatus, name="listing_status_enum"),
        nullable=False,
        default=ListingStatus.DRAFT,
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    ownership: Mapped["Ownership"] = relationship(back_populates="listings")
    seller_company: Mapped["Company"] = relationship(back_populates="listings")
    purchase_orders: Mapped[List["PurchaseOrder"]] = relationship(back_populates="listing", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("credits_for_sale > 0", name="chk_listings_credits_for_sale_positive"),
        CheckConstraint("price_per_credit > 0", name="chk_listings_price_per_credit_positive"),
        CheckConstraint("minimum_purchase >= 1", name="chk_listings_minimum_purchase_limit"),
        Index("idx_marketplace_listings_status", "status"),
    )


class PurchaseOrder(Base, PrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "purchase_orders"

    listing_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("marketplace_listings.id", ondelete="RESTRICT"),
        nullable=False,
    )
    buyer_company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"),
        nullable=False,
    )
    requested_credits: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    price_per_credit: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    total_price: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        Enum(PurchaseOrderStatus, name="purchase_order_status_enum"),
        nullable=False,
        default=PurchaseOrderStatus.PENDING,
    )
    payment_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    listing: Mapped["MarketplaceListing"] = relationship(back_populates="purchase_orders")
    buyer_company: Mapped["Company"] = relationship(back_populates="purchase_orders")
    transaction: Mapped[Optional["Transaction"]] = relationship(back_populates="purchase_order", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("requested_credits > 0", name="chk_orders_requested_credits_positive"),
        CheckConstraint("price_per_credit > 0", name="chk_orders_price_per_credit_positive"),
        CheckConstraint("total_price > 0", name="chk_orders_total_price_positive"),
        Index("idx_purchase_orders_status", "status"),
    )


class Transaction(Base, PrimaryKeyMixin, TimestampMixin):
    __tablename__ = "transactions"

    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="RESTRICT"),
        nullable=False,
    )
    buyer_company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"),
        nullable=False,
    )
    seller_company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"),
        nullable=False,
    )
    ownership_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ownerships.id", ondelete="RESTRICT"),
        nullable=False,
    )
    credits_transferred: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    price_per_credit: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    total_price: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    blockchain_tx_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    blockchain_status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")
    block_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    blockchain_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(back_populates="transaction")
    seller_company: Mapped["Company"] = relationship(foreign_keys=[seller_company_id], back_populates="sent_transactions")
    buyer_company: Mapped["Company"] = relationship(foreign_keys=[buyer_company_id], back_populates="received_transactions")
    ownership: Mapped["Ownership"] = relationship(back_populates="transactions")

    __table_args__ = (
        UniqueConstraint("order_id", name="uq_transactions_order_id"),
        UniqueConstraint("blockchain_tx_hash", name="uq_transactions_blockchain_tx_hash"),
        CheckConstraint("credits_transferred > 0", name="chk_transactions_credits_transferred_positive"),
        CheckConstraint("price_per_credit > 0", name="chk_transactions_price_per_credit_positive"),
        CheckConstraint("total_price > 0", name="chk_transactions_total_price_positive"),
        Index("idx_transactions_status", "status"),
        Index("idx_transactions_blockchain_tx_hash", "blockchain_tx_hash"),
    )


class Retirement(Base, PrimaryKeyMixin, TimestampMixin):
    __tablename__ = "retirements"

    ownership_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ownerships.id", ondelete="RESTRICT"),
        nullable=False,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"),
        nullable=False,
    )
    credits_retired: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    certificate_number: Mapped[str] = mapped_column(String(100), nullable=False)
    blockchain_tx_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    retired_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
    )
    blockchain_status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")
    block_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    blockchain_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    ownership: Mapped["Ownership"] = relationship(back_populates="retirements")
    company: Mapped["Company"] = relationship(back_populates="retirements")

    __table_args__ = (
        UniqueConstraint("certificate_number", name="uq_retirements_certificate_number"),
        UniqueConstraint("blockchain_tx_hash", name="uq_retirements_blockchain_tx_hash"),
        CheckConstraint("credits_retired > 0", name="chk_retirements_credits_retired_positive"),
        Index("idx_retirements_certificate_number", "certificate_number"),
        Index("idx_retirements_blockchain_tx_hash", "blockchain_tx_hash"),
    )


class AuditLog(Base, PrimaryKeyMixin):
    __tablename__ = "audit_logs"

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("companies.id", ondelete="SET NULL"),
        nullable=True,
    )
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    old_values: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    new_values: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # Support IPv6
    user_agent: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
    )
    blockchain_status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")
    blockchain_tx_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    block_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    blockchain_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped[Optional["User"]] = relationship(back_populates="audit_logs")
    company: Mapped[Optional["Company"]] = relationship(back_populates="audit_logs")

    __table_args__ = (
        Index("idx_audit_logs_user_id", "user_id"),
        Index("idx_audit_logs_company_id", "company_id"),
        Index("idx_audit_logs_entity", "entity_type", "entity_id"),
        Index("idx_audit_logs_timestamp", "timestamp"),
    )


class RefreshToken(Base, PrimaryKeyMixin, TimestampMixin):
    __tablename__ = "refresh_tokens"

    token_jti: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reused_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="refresh_tokens")

    __table_args__ = (
        UniqueConstraint("token_jti", name="uq_refresh_tokens_token_jti"),
        Index("idx_refresh_tokens_token_jti", "token_jti"),
        Index("idx_refresh_tokens_user_id", "user_id"),
    )
