import uuid
from typing import Optional, Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import PermissionDeniedException, BusinessRuleException, NotFoundException
from app.core.dependencies import get_current_active_user, get_pagination_params
from app.schemas.pagination import PaginationParams
from app.schemas.responses import APIResponse
from app.models.models import User, UserRole
from app.services.services import AdminService, AuditService
from app.repositories.repositories import AuditRepository

router = APIRouter(prefix="/admin", tags=["System Administration"])


def check_admin_permission(current_user: User = Depends(get_current_active_user)) -> None:
    if current_user.role != UserRole.ADMIN:
        raise PermissionDeniedException("Only system administrators have access to this module")


def get_admin_service(db: Session = Depends(get_db)) -> AdminService:
    return AdminService(db)


def get_audit_service(db: Session = Depends(get_db)) -> AuditService:
    return AuditService(AuditRepository(db))


@router.get("/dashboard", response_model=APIResponse[dict], dependencies=[Depends(check_admin_permission)])
def get_admin_dashboard(
    service: AdminService = Depends(get_admin_service)
):
    """
    Retrieves global administration metrics across all entities.
    """
    data = service.get_dashboard()
    return {
        "success": True,
        "message": "Admin dashboard metrics compiled successfully",
        "data": data
    }


@router.get("/users", response_model=APIResponse[dict], dependencies=[Depends(check_admin_permission)])
def list_all_users(
    search: Optional[str] = Query(None),
    pagination: PaginationParams = Depends(get_pagination_params),
    service: AdminService = Depends(get_admin_service)
):
    """
    Paginated lists of system users with filter capabilities.
    """
    items, total = service.list_users(search=search, skip=(pagination.page - 1) * pagination.limit, limit=pagination.limit)
    data = []
    for u in items:
        data.append({
            "id": str(u.id),
            "first_name": u.first_name,
            "last_name": u.last_name,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
            "company_id": str(u.company_id) if u.company_id else None,
            "created_at": u.created_at.isoformat()
        })
    return {
        "success": True,
        "message": "Users list retrieved successfully",
        "data": {
            "items": data,
            "total": total,
            "page": pagination.page,
            "limit": pagination.limit
        }
    }


@router.get("/companies", response_model=APIResponse[dict], dependencies=[Depends(check_admin_permission)])
def list_all_companies(
    search: Optional[str] = Query(None),
    pagination: PaginationParams = Depends(get_pagination_params),
    service: AdminService = Depends(get_admin_service)
):
    """
    Paginated lists of registered companies.
    """
    items, total = service.list_companies(search=search, skip=(pagination.page - 1) * pagination.limit, limit=pagination.limit)
    data = []
    for c in items:
        data.append({
            "id": str(c.id),
            "name": c.name,
            "registration_number": c.registration_number,
            "country": c.country,
            "status": c.status,
            "is_active": c.is_active,
            "created_at": c.created_at.isoformat()
        })
    return {
        "success": True,
        "message": "Companies list retrieved successfully",
        "data": {
            "items": data,
            "total": total,
            "page": pagination.page,
            "limit": pagination.limit
        }
    }


@router.get("/registries", response_model=APIResponse[dict], dependencies=[Depends(check_admin_permission)])
def list_all_registries(
    search: Optional[str] = Query(None),
    pagination: PaginationParams = Depends(get_pagination_params),
    service: AdminService = Depends(get_admin_service)
):
    """
    Paginated lists of carbon registries.
    """
    items, total = service.list_registries(search=search, skip=(pagination.page - 1) * pagination.limit, limit=pagination.limit)
    data = []
    for r in items:
        data.append({
            "id": str(r.id),
            "name": r.name,
            "country": r.country,
            "website": r.website,
            "accreditation": r.accreditation,
            "is_active": r.is_active,
            "created_at": r.created_at.isoformat()
        })
    return {
        "success": True,
        "message": "Registries list retrieved successfully",
        "data": {
            "items": data,
            "total": total,
            "page": pagination.page,
            "limit": pagination.limit
        }
    }


@router.get("/projects", response_model=APIResponse[dict], dependencies=[Depends(check_admin_permission)])
def list_all_projects(
    search: Optional[str] = Query(None),
    pagination: PaginationParams = Depends(get_pagination_params),
    service: AdminService = Depends(get_admin_service)
):
    """
    Paginated lists of carbon projects.
    """
    items, total = service.list_projects(search=search, skip=(pagination.page - 1) * pagination.limit, limit=pagination.limit)
    data = []
    for p in items:
        data.append({
            "id": str(p.id),
            "registry_id": str(p.registry_id),
            "project_code": p.project_code,
            "name": p.name,
            "country": p.country,
            "project_type": p.project_type,
            "verification_standard": p.verification_standard,
            "status": p.status,
            "is_active": p.is_active,
            "created_at": p.created_at.isoformat()
        })
    return {
        "success": True,
        "message": "Projects list retrieved successfully",
        "data": {
            "items": data,
            "total": total,
            "page": pagination.page,
            "limit": pagination.limit
        }
    }


@router.get("/batches", response_model=APIResponse[dict], dependencies=[Depends(check_admin_permission)])
def list_all_batches(
    search: Optional[str] = Query(None),
    pagination: PaginationParams = Depends(get_pagination_params),
    service: AdminService = Depends(get_admin_service)
):
    """
    Paginated lists of credit batches.
    """
    items, total = service.list_batches(search=search, skip=(pagination.page - 1) * pagination.limit, limit=pagination.limit)
    data = []
    for b in items:
        data.append({
            "id": str(b.id),
            "project_id": str(b.project_id),
            "batch_number": b.batch_number,
            "vintage_year": b.vintage_year,
            "total_credits": float(b.total_credits),
            "remaining_credits": float(b.remaining_credits),
            "status": b.status,
            "is_active": b.is_active,
            "created_at": b.created_at.isoformat()
        })
    return {
        "success": True,
        "message": "Batches list retrieved successfully",
        "data": {
            "items": data,
            "total": total,
            "page": pagination.page,
            "limit": pagination.limit
        }
    }


@router.get("/listings", response_model=APIResponse[dict], dependencies=[Depends(check_admin_permission)])
def list_all_listings(
    search: Optional[str] = Query(None),
    pagination: PaginationParams = Depends(get_pagination_params),
    service: AdminService = Depends(get_admin_service)
):
    """
    Paginated lists of marketplace listings.
    """
    items, total = service.list_listings(search=search, skip=(pagination.page - 1) * pagination.limit, limit=pagination.limit)
    data = []
    for l in items:
        data.append({
            "id": str(l.id),
            "ownership_id": str(l.ownership_id),
            "seller_company_id": str(l.seller_company_id),
            "credits_for_sale": float(l.credits_for_sale),
            "price_per_credit": float(l.price_per_credit),
            "status": l.status,
            "created_at": l.created_at.isoformat()
        })
    return {
        "success": True,
        "message": "Listings list retrieved successfully",
        "data": {
            "items": data,
            "total": total,
            "page": pagination.page,
            "limit": pagination.limit
        }
    }


@router.get("/orders", response_model=APIResponse[dict], dependencies=[Depends(check_admin_permission)])
def list_all_orders(
    search: Optional[str] = Query(None),
    pagination: PaginationParams = Depends(get_pagination_params),
    service: AdminService = Depends(get_admin_service)
):
    """
    Paginated lists of purchase orders.
    """
    items, total = service.list_orders(search=search, skip=(pagination.page - 1) * pagination.limit, limit=pagination.limit)
    data = []
    for o in items:
        data.append({
            "id": str(o.id),
            "listing_id": str(o.listing_id),
            "buyer_company_id": str(o.buyer_company_id),
            "requested_credits": float(o.requested_credits),
            "price_per_credit": float(o.price_per_credit),
            "total_price": float(o.total_price),
            "status": o.status,
            "created_at": o.created_at.isoformat()
        })
    return {
        "success": True,
        "message": "Orders list retrieved successfully",
        "data": {
            "items": data,
            "total": total,
            "page": pagination.page,
            "limit": pagination.limit
        }
    }


@router.get("/transactions", response_model=APIResponse[dict], dependencies=[Depends(check_admin_permission)])
def list_all_transactions(
    search: Optional[str] = Query(None),
    pagination: PaginationParams = Depends(get_pagination_params),
    service: AdminService = Depends(get_admin_service)
):
    """
    Paginated lists of completed transactions.
    """
    items, total = service.list_transactions(search=search, skip=(pagination.page - 1) * pagination.limit, limit=pagination.limit)
    data = []
    for t in items:
        data.append({
            "id": str(t.id),
            "order_id": str(t.order_id),
            "buyer_company_id": str(t.buyer_company_id),
            "seller_company_id": str(t.seller_company_id),
            "credits_transferred": float(t.credits_transferred),
            "price_per_credit": float(t.price_per_credit),
            "total_price": float(t.total_price),
            "status": t.status,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None
        })
    return {
        "success": True,
        "message": "Transactions list retrieved successfully",
        "data": {
            "items": data,
            "total": total,
            "page": pagination.page,
            "limit": pagination.limit
        }
    }


@router.get("/retirements", response_model=APIResponse[dict], dependencies=[Depends(check_admin_permission)])
def list_all_retirements(
    search: Optional[str] = Query(None),
    pagination: PaginationParams = Depends(get_pagination_params),
    service: AdminService = Depends(get_admin_service)
):
    """
    Paginated lists of retirements.
    """
    items, total = service.list_retirements(search=search, skip=(pagination.page - 1) * pagination.limit, limit=pagination.limit)
    data = []
    for r in items:
        data.append({
            "id": str(r.id),
            "ownership_id": str(r.ownership_id),
            "company_id": str(r.company_id),
            "credits_retired": float(r.credits_retired),
            "reason": r.reason,
            "certificate_number": r.certificate_number,
            "retired_at": r.retired_at.isoformat()
        })
    return {
        "success": True,
        "message": "Retirements list retrieved successfully",
        "data": {
            "items": data,
            "total": total,
            "page": pagination.page,
            "limit": pagination.limit
        }
    }


@router.patch("/users/{user_id}/activate", response_model=APIResponse[dict], dependencies=[Depends(check_admin_permission)])
def activate_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    service: AdminService = Depends(get_admin_service)
):
    """
    Administratively activates a user account.
    """
    user = service.activate_user(user_id, current_user.id)
    return {
        "success": True,
        "message": "User activated successfully",
        "data": {
            "id": str(user.id),
            "is_active": user.is_active
        }
    }


@router.patch("/users/{user_id}/deactivate", response_model=APIResponse[dict], dependencies=[Depends(check_admin_permission)])
def deactivate_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    service: AdminService = Depends(get_admin_service)
):
    """
    Administratively deactivates/suspends a user account.
    """
    user = service.deactivate_user(user_id, current_user.id)
    return {
        "success": True,
        "message": "User deactivated successfully",
        "data": {
            "id": str(user.id),
            "is_active": user.is_active
        }
    }


@router.patch("/companies/{company_id}/activate", response_model=APIResponse[dict], dependencies=[Depends(check_admin_permission)])
def activate_company(
    company_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    service: AdminService = Depends(get_admin_service)
):
    """
    Administratively activates a company.
    """
    company = service.activate_company(company_id, current_user.id)
    return {
        "success": True,
        "message": "Company activated successfully",
        "data": {
            "id": str(company.id),
            "is_active": company.is_active,
            "status": company.status
        }
    }


@router.patch("/companies/{company_id}/deactivate", response_model=APIResponse[dict], dependencies=[Depends(check_admin_permission)])
def deactivate_company(
    company_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    service: AdminService = Depends(get_admin_service)
):
    """
    Administratively deactivates/suspends a company.
    """
    company = service.deactivate_company(company_id, current_user.id)
    return {
        "success": True,
        "message": "Company deactivated successfully",
        "data": {
            "id": str(company.id),
            "is_active": company.is_active,
            "status": company.status
        }
    }


@router.get("/audit-logs", response_model=APIResponse[dict], dependencies=[Depends(check_admin_permission)])
def list_audit_logs(
    search: Optional[str] = Query(None),
    company_id: Optional[uuid.UUID] = Query(None),
    user_id: Optional[uuid.UUID] = Query(None),
    action: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    pagination: PaginationParams = Depends(get_pagination_params),
    service: AuditService = Depends(get_audit_service)
):
    """
    Retrieves system audit logs. Support filtering by search term, user, company, action, and date range.
    """
    from datetime import datetime
    s_date = None
    e_date = None
    if start_date:
        try:
            s_date = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        except ValueError:
            raise BusinessRuleException("Invalid start_date format")
    if end_date:
        try:
            e_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        except ValueError:
            raise BusinessRuleException("Invalid end_date format")

    items, total = service.list_audit_logs(
        search=search,
        filter_company=company_id,
        filter_user=user_id,
        action=action,
        start_date=s_date,
        end_date=e_date,
        skip=(pagination.page - 1) * pagination.limit,
        limit=pagination.limit
    )

    data = []
    for log in items:
        data.append({
            "id": str(log.id),
            "user_id": str(log.user_id) if log.user_id else None,
            "company_id": str(log.company_id) if log.company_id else None,
            "entity_type": log.entity_type,
            "entity_id": str(log.entity_id) if log.entity_id else None,
            "action": log.action,
            "old_values": log.old_values,
            "new_values": log.new_values,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "timestamp": log.timestamp.isoformat()
        })

    return {
        "success": True,
        "message": "Audit logs compiled successfully",
        "data": {
            "items": data,
            "total": total,
            "page": pagination.page,
            "limit": pagination.limit
        }
    }


@router.get("/audit-logs/{log_id}", response_model=APIResponse[dict], dependencies=[Depends(check_admin_permission)])
def get_audit_log_detail(
    log_id: uuid.UUID,
    service: AuditService = Depends(get_audit_service)
):
    """
    Retrieves details of a single audit log entry.
    """
    log = service.repository.find_by_id(log_id)
    if not log:
        raise NotFoundException(f"Audit log entry with ID {log_id} not found")

    return {
        "success": True,
        "message": "Audit log entry details retrieved successfully",
        "data": {
            "id": str(log.id),
            "user_id": str(log.user_id) if log.user_id else None,
            "company_id": str(log.company_id) if log.company_id else None,
            "entity_type": log.entity_type,
            "entity_id": str(log.entity_id) if log.entity_id else None,
            "action": log.action,
            "old_values": log.old_values,
            "new_values": log.new_values,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "timestamp": log.timestamp.isoformat()
        }
    }
