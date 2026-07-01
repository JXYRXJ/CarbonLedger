from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
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
    RefreshToken
)


class CompanyRepository(BaseRepository[Company]):
    def __init__(self, db: Session) -> None:
        super().__init__(Company, db)


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session) -> None:
        super().__init__(User, db)


from typing import List, Optional, Tuple, Any

class RegistryRepository(BaseRepository[Registry]):
    def __init__(self, db: Session) -> None:
        super().__init__(Registry, db)

    def find_by_name(self, name: str) -> Optional[Registry]:
        return self.find_one(name=name)

    def find_all(self) -> List[Registry]:
        return self.find_many(limit=1000)

    def search(
        self,
        search_query: Optional[str] = None,
        status: Optional[str] = None,
        country: Optional[str] = None,
        accreditation: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        sort_field: Optional[str] = None,
        sort_order: str = "asc"
    ) -> Tuple[List[Registry], int]:
        from sqlalchemy import select, func, or_
        stmt = select(Registry).where(Registry.deleted_at == None)
        
        if status:
            stmt = stmt.where(Registry.status == status)
        if country:
            stmt = stmt.where(Registry.country.ilike(f"%{country}%"))
        if accreditation:
            stmt = stmt.where(Registry.accreditation.ilike(f"%{accreditation}%"))
        if search_query:
            stmt = stmt.where(
                or_(
                    Registry.name.ilike(f"%{search_query}%"),
                    Registry.country.ilike(f"%{search_query}%"),
                    Registry.accreditation.ilike(f"%{search_query}%")
                )
            )
        
        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar() or 0
        
        # Sort
        if sort_field and hasattr(Registry, sort_field):
            col = getattr(Registry, sort_field)
            if sort_order.lower() == "desc":
                stmt = stmt.order_by(col.desc())
            else:
                stmt = stmt.order_by(col.asc())
        else:
            stmt = stmt.order_by(Registry.name.asc())
            
        stmt = stmt.offset(skip).limit(limit)
        items = list(self.db.execute(stmt).scalars().all())
        return items, total


class ProjectRepository(BaseRepository[CarbonProject]):
    def __init__(self, db: Session) -> None:
        super().__init__(CarbonProject, db)

    def find_by_project_code(self, project_code: str) -> Optional[CarbonProject]:
        return self.find_one(project_code=project_code)

    def find_all(self) -> List[CarbonProject]:
        return self.find_many(limit=1000)

    def search(
        self,
        search_query: Optional[str] = None,
        country: Optional[str] = None,
        registry_id: Optional[str] = None,
        verification_standard: Optional[str] = None,
        project_type: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        sort_field: Optional[str] = None,
        sort_order: str = "asc"
    ) -> Tuple[List[CarbonProject], int]:
        from sqlalchemy import select, func, or_
        import uuid
        stmt = select(CarbonProject).where(CarbonProject.deleted_at == None)
        
        if status:
            stmt = stmt.where(CarbonProject.status == status)
        if country:
            stmt = stmt.where(CarbonProject.country.ilike(f"%{country}%"))
        if registry_id:
            try:
                reg_uuid = uuid.UUID(str(registry_id))
                stmt = stmt.where(CarbonProject.registry_id == reg_uuid)
            except ValueError:
                pass
        if verification_standard:
            stmt = stmt.where(CarbonProject.verification_standard.ilike(f"%{verification_standard}%"))
        if project_type:
            stmt = stmt.where(CarbonProject.project_type.ilike(f"%{project_type}%"))
        if search_query:
            stmt = stmt.where(
                or_(
                    CarbonProject.name.ilike(f"%{search_query}%"),
                    CarbonProject.project_code.ilike(f"%{search_query}%"),
                    CarbonProject.country.ilike(f"%{search_query}%"),
                    CarbonProject.verification_standard.ilike(f"%{search_query}%"),
                    CarbonProject.project_type.ilike(f"%{search_query}%")
                )
            )
            
        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar() or 0
        
        # Sort
        if sort_field and hasattr(CarbonProject, sort_field):
            col = getattr(CarbonProject, sort_field)
            if sort_order.lower() == "desc":
                stmt = stmt.order_by(col.desc())
            else:
                stmt = stmt.order_by(col.asc())
        else:
            stmt = stmt.order_by(CarbonProject.created_at.desc())
            
        stmt = stmt.offset(skip).limit(limit)
        items = list(self.db.execute(stmt).scalars().all())
        return items, total


class DocumentRepository(BaseRepository[ProjectDocument]):
    def __init__(self, db: Session) -> None:
        super().__init__(ProjectDocument, db)

    def find_by_project(self, project_id: Any) -> List[ProjectDocument]:
        from sqlalchemy import select
        import uuid
        try:
            proj_uuid = uuid.UUID(str(project_id))
        except ValueError:
            return []
        stmt = select(ProjectDocument).where(ProjectDocument.project_id == proj_uuid)
        return list(self.db.execute(stmt).scalars().all())



class BatchRepository(BaseRepository[CreditBatch]):
    def __init__(self, db: Session) -> None:
        super().__init__(CreditBatch, db)

    def find_by_batch_number(self, batch_number: str) -> Optional[CreditBatch]:
        return self.find_one(batch_number=batch_number)

    def search(
        self,
        search_query: Optional[str] = None,
        registry_id: Optional[str] = None,
        country: Optional[str] = None,
        project_type: Optional[str] = None,
        verification_standard: Optional[str] = None,
        vintage_year: Optional[int] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        sort_field: Optional[str] = None,
        sort_order: str = "asc"
    ) -> Tuple[List[CreditBatch], int]:
        from sqlalchemy import select, func, or_
        import uuid
        from app.models.models import CarbonProject, Registry
        
        stmt = select(CreditBatch).join(CarbonProject).join(Registry)
        
        if status:
            stmt = stmt.where(CreditBatch.status == status)
        if vintage_year is not None:
            stmt = stmt.where(CreditBatch.vintage_year == vintage_year)
        if country:
            stmt = stmt.where(CarbonProject.country.ilike(f"%{country}%"))
        if project_type:
            stmt = stmt.where(CarbonProject.project_type.ilike(f"%{project_type}%"))
        if verification_standard:
            stmt = stmt.where(CarbonProject.verification_standard.ilike(f"%{verification_standard}%"))
        if registry_id:
            try:
                reg_uuid = uuid.UUID(str(registry_id))
                stmt = stmt.where(CarbonProject.registry_id == reg_uuid)
            except ValueError:
                pass
                
        if search_query:
            stmt = stmt.where(
                or_(
                    CreditBatch.batch_number.ilike(f"%{search_query}%"),
                    CarbonProject.name.ilike(f"%{search_query}%"),
                    Registry.name.ilike(f"%{search_query}%"),
                    CarbonProject.country.ilike(f"%{search_query}%"),
                    CarbonProject.verification_standard.ilike(f"%{search_query}%")
                )
            )
            
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar() or 0
        
        if sort_field and hasattr(CreditBatch, sort_field):
            col = getattr(CreditBatch, sort_field)
            if sort_order.lower() == "desc":
                stmt = stmt.order_by(col.desc())
            else:
                stmt = stmt.order_by(col.asc())
        elif sort_field == "created_date":
            if sort_order.lower() == "desc":
                stmt = stmt.order_by(CreditBatch.created_at.desc())
            else:
                stmt = stmt.order_by(CreditBatch.created_at.asc())
        else:
            stmt = stmt.order_by(CreditBatch.batch_number.asc())
            
        stmt = stmt.offset(skip).limit(limit)
        items = list(self.db.execute(stmt).scalars().all())
        return items, total


class OwnershipRepository(BaseRepository[Ownership]):
    def __init__(self, db: Session) -> None:
        super().__init__(Ownership, db)

    def find_by_company(self, company_id: Any) -> List[Ownership]:
        import uuid
        from sqlalchemy import select
        try:
            comp_uuid = uuid.UUID(str(company_id))
        except ValueError:
            return []
        stmt = select(Ownership).where(Ownership.company_id == comp_uuid)
        return list(self.db.execute(stmt).scalars().all())

    def find_by_batch(self, batch_id: Any) -> List[Ownership]:
        import uuid
        from sqlalchemy import select
        try:
            batch_uuid = uuid.UUID(str(batch_id))
        except ValueError:
            return []
        stmt = select(Ownership).where(Ownership.batch_id == batch_uuid)
        return list(self.db.execute(stmt).scalars().all())



class MarketplaceRepository(BaseRepository[MarketplaceListing]):
    def __init__(self, db: Session) -> None:
        super().__init__(MarketplaceListing, db)

    def search(
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
        from sqlalchemy import select, func, or_
        import uuid
        from app.models.models import Ownership, CreditBatch, CarbonProject, Registry, Company
        
        stmt = select(MarketplaceListing)\
            .join(Ownership)\
            .join(CreditBatch)\
            .join(CarbonProject)\
            .join(Registry)\
            .outerjoin(Company, Company.id == MarketplaceListing.seller_company_id)\
            .where(MarketplaceListing.deleted_at == None)
        
        if status:
            stmt = stmt.where(MarketplaceListing.status == status)
        if vintage_year is not None:
            stmt = stmt.where(CreditBatch.vintage_year == vintage_year)
        if country:
            stmt = stmt.where(CarbonProject.country.ilike(f"%{country}%"))
        if project_type:
            stmt = stmt.where(CarbonProject.project_type.ilike(f"%{project_type}%"))
        if verification_standard:
            stmt = stmt.where(CarbonProject.verification_standard.ilike(f"%{verification_standard}%"))
        if registry_id:
            try:
                reg_uuid = uuid.UUID(str(registry_id))
                stmt = stmt.where(CarbonProject.registry_id == reg_uuid)
            except ValueError:
                pass
                
        if min_price is not None:
            stmt = stmt.where(MarketplaceListing.price_per_credit >= min_price)
        if max_price is not None:
            stmt = stmt.where(MarketplaceListing.price_per_credit <= max_price)
        if min_credits is not None:
            stmt = stmt.where(MarketplaceListing.credits_for_sale >= min_credits)
            
        if search_query:
            stmt = stmt.where(
                or_(
                    CreditBatch.batch_number.ilike(f"%{search_query}%"),
                    CarbonProject.name.ilike(f"%{search_query}%"),
                    Registry.name.ilike(f"%{search_query}%"),
                    Company.name.ilike(f"%{search_query}%"),
                    CarbonProject.country.ilike(f"%{search_query}%"),
                    CarbonProject.verification_standard.ilike(f"%{search_query}%")
                )
            )
            
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar() or 0
        
        # Sorting
        if sort_field == "newest":
            stmt = stmt.order_by(MarketplaceListing.created_at.desc())
        elif sort_field == "oldest":
            stmt = stmt.order_by(MarketplaceListing.created_at.asc())
        elif sort_field == "lowest_price":
            stmt = stmt.order_by(MarketplaceListing.price_per_credit.asc())
        elif sort_field == "highest_price":
            stmt = stmt.order_by(MarketplaceListing.price_per_credit.desc())
        elif sort_field == "available_credits":
            stmt = stmt.order_by(MarketplaceListing.credits_for_sale.desc())
        else:
            stmt = stmt.order_by(MarketplaceListing.created_at.desc())
            
        stmt = stmt.offset(skip).limit(limit)
        items = list(self.db.execute(stmt).scalars().all())
        return items, total


class OrderRepository(BaseRepository[PurchaseOrder]):
    def __init__(self, db: Session) -> None:
        super().__init__(PurchaseOrder, db)

    def find_by_buyer_company(self, company_id: Any) -> List[PurchaseOrder]:
        import uuid
        from sqlalchemy import select
        try:
            comp_uuid = uuid.UUID(str(company_id))
        except ValueError:
            return []
        stmt = select(PurchaseOrder).where(PurchaseOrder.buyer_company_id == comp_uuid)
        return list(self.db.execute(stmt).scalars().all())


class TransactionRepository(BaseRepository[Transaction]):
    def __init__(self, db: Session) -> None:
        super().__init__(Transaction, db)

    def find_by_company(self, company_id: Any) -> List[Transaction]:
        import uuid
        from sqlalchemy import select, or_
        try:
            comp_uuid = uuid.UUID(str(company_id))
        except ValueError:
            return []
        stmt = select(Transaction).where(
            or_(
                Transaction.buyer_company_id == comp_uuid,
                Transaction.seller_company_id == comp_uuid
            )
        )
        return list(self.db.execute(stmt).scalars().all())


class RetirementRepository(BaseRepository[Retirement]):
    def __init__(self, db: Session) -> None:
        super().__init__(Retirement, db)

    def find_by_company(self, company_id: Any) -> List[Retirement]:
        import uuid
        from sqlalchemy import select
        try:
            comp_uuid = uuid.UUID(str(company_id))
        except ValueError:
            return []
        stmt = select(Retirement).where(Retirement.company_id == comp_uuid)
        return list(self.db.execute(stmt).scalars().all())

    def find_by_certificate(self, certificate_number: str) -> Optional[Retirement]:
        from sqlalchemy import select
        stmt = select(Retirement).where(Retirement.certificate_number == certificate_number)
        return self.db.execute(stmt).scalar_one_or_none()

    def search(
        self,
        cert_number: Optional[str] = None,
        batch_number: Optional[str] = None,
        company_name: Optional[str] = None,
        start_date: Optional[Any] = None,
        end_date: Optional[Any] = None
    ) -> List[Retirement]:
        from sqlalchemy import select
        from app.models.models import Company, Ownership, CreditBatch
        stmt = select(Retirement).outerjoin(Company, Company.id == Retirement.company_id)\
            .outerjoin(Ownership, Ownership.id == Retirement.ownership_id)\
            .outerjoin(CreditBatch, CreditBatch.id == Ownership.batch_id)
            
        if cert_number:
            stmt = stmt.where(Retirement.certificate_number.ilike(f"%{cert_number}%"))
        if batch_number:
            stmt = stmt.where(CreditBatch.batch_number.ilike(f"%{batch_number}%"))
        if company_name:
            stmt = stmt.where(Company.name.ilike(f"%{company_name}%"))
        if start_date:
            stmt = stmt.where(Retirement.retired_at >= start_date)
        if end_date:
            stmt = stmt.where(Retirement.retired_at <= end_date)
            
        return list(self.db.execute(stmt).scalars().all())


class AuditRepository(BaseRepository[AuditLog]):
    def __init__(self, db: Session) -> None:
        super().__init__(AuditLog, db)


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def __init__(self, db: Session) -> None:
        super().__init__(RefreshToken, db)
