import uuid
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from app.core.database import get_db
from app.core.exceptions import PermissionDeniedException, BusinessRuleException, NotFoundException
from app.core.dependencies import get_current_active_user
from app.models.models import User, UserRole, Transaction, Company, Ownership, CreditBatch, CarbonProject, Registry, Retirement, AuditLog
from app.services.export import ExportService

router = APIRouter(prefix="/exports", tags=["Exports & Reporting"])


def get_export_service() -> ExportService:
    return ExportService()


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        raise BusinessRuleException(f"Invalid date format: '{date_str}'")


@router.get("/transactions")
def export_transactions(
    format: str = Query("csv", pattern="^(csv|excel|pdf)$"),
    company_id: Optional[uuid.UUID] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    exporter: ExportService = Depends(get_export_service)
):
    """
    Exports a list of carbon credit transactions matching the filters.
    """
    # 1. Scope checks
    target_company_id = company_id
    if current_user.role not in [UserRole.ADMIN, UserRole.AUDITOR]:
        if not current_user.company_id:
            raise PermissionDeniedException("User must belong to a company to export transactions")
        target_company_id = current_user.company_id

    # 2. Build Query
    from sqlalchemy.orm import joinedload
    stmt = select(Transaction).options(
        joinedload(Transaction.buyer_company),
        joinedload(Transaction.seller_company)
    ).join(Company, or_(Company.id == Transaction.buyer_company_id, Company.id == Transaction.seller_company_id))
    
    if target_company_id:
        stmt = stmt.where(or_(
            Transaction.buyer_company_id == target_company_id,
            Transaction.seller_company_id == target_company_id
        ))
        
    if status:
        stmt = stmt.where(Transaction.status == status)
        
    s_date = parse_date(start_date)
    e_date = parse_date(end_date)
    if s_date:
        stmt = stmt.where(Transaction.completed_at >= s_date)
    if e_date:
        stmt = stmt.where(Transaction.completed_at <= e_date)
        
    if search:
        stmt = stmt.where(Company.name.ilike(f"%{search}%"))
        
    stmt = stmt.order_by(Transaction.completed_at.desc())
    transactions = db.execute(stmt).scalars().all()

    # 3. Format Data
    headers = [
        "Transaction ID", "Buyer Company", "Seller Company", "Credits Transferred",
        "Price Per Credit", "Total Price", "Status", "Completion Date"
    ]
    rows = []
    for tx in transactions:
        buyer_name = tx.buyer_company.name if tx.buyer_company else "Unknown"
        seller_name = tx.seller_company.name if tx.seller_company else "Unknown"
        rows.append([
            str(tx.id),
            buyer_name,
            seller_name,
            float(tx.credits_transferred),
            float(tx.price_per_credit),
            float(tx.total_price),
            tx.status,
            tx.completed_at
        ])

    # 4. Generate Response
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if format == "csv":
        data_bytes = exporter.export_to_csv(headers, rows)
        return Response(
            content=data_bytes,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=transactions_{timestamp}.csv"}
        )
    elif format == "excel":
        data_bytes = exporter.export_to_excel("Transactions", headers, rows, totals_cols=[3, 5])
        return Response(
            content=data_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=transactions_{timestamp}.xlsx"}
        )
    else:
        # PDF
        data_bytes = exporter.export_to_pdf(
            "Completed Carbon Transactions Report",
            headers,
            rows,
            company_info={"name": "System Export", "id": str(current_user.id)}
        )
        return Response(
            content=data_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=transactions_{timestamp}.pdf"}
        )


@router.get("/portfolio")
def export_portfolio(
    format: str = Query("csv", pattern="^(csv|excel|pdf)$"),
    company_id: Optional[uuid.UUID] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    exporter: ExportService = Depends(get_export_service)
):
    """
    Exports the portfolio holdings of a company.
    """
    target_company_id = company_id
    if current_user.role not in [UserRole.ADMIN, UserRole.AUDITOR]:
        if not current_user.company_id:
            raise PermissionDeniedException("User must belong to a company to export portfolio")
        target_company_id = current_user.company_id
    else:
        if not target_company_id:
            raise BusinessRuleException("Admins/Auditors must specify a company_id query parameter")

    # Fetch holdings
    from sqlalchemy.orm import joinedload
    holdings = db.query(Ownership).filter(Ownership.company_id == target_company_id)\
        .options(
            joinedload(Ownership.batch)
            .joinedload(CreditBatch.project)
            .joinedload(CarbonProject.registry)
        ).all()
    comp_name = db.query(Company.name).filter(Company.id == target_company_id).scalar() or "N/A"

    headers = [
        "Batch Number", "Project Code", "Project Name", "Registry",
        "Vintage Year", "Owned Credits", "Average Purchase Price", "Est Value"
    ]
    rows = []
    for own in holdings:
        batch = own.batch
        project = batch.project if batch else None
        registry = project.registry if project else None
        rows.append([
            batch.batch_number if batch else "Unknown",
            project.project_code if project else "N/A",
            project.name if project else "N/A",
            registry.name if registry else "N/A",
            batch.vintage_year if batch else 0,
            float(own.owned_credits),
            float(own.average_purchase_price),
            float(own.owned_credits * own.average_purchase_price)
        ])

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if format == "csv":
        data_bytes = exporter.export_to_csv(headers, rows)
        return Response(
            content=data_bytes,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=portfolio_{timestamp}.csv"}
        )
    elif format == "excel":
        data_bytes = exporter.export_to_excel("Portfolio", headers, rows, totals_cols=[5, 7])
        return Response(
            content=data_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=portfolio_{timestamp}.xlsx"}
        )
    else:
        data_bytes = exporter.export_to_pdf(
            f"Carbon Asset Portfolio: {comp_name}",
            headers,
            rows,
            company_info={"name": comp_name, "id": str(target_company_id)}
        )
        return Response(
            content=data_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=portfolio_{timestamp}.pdf"}
        )


@router.get("/retirements")
def export_retirements(
    format: str = Query("csv", pattern="^(csv|excel|pdf)$"),
    company_id: Optional[uuid.UUID] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    exporter: ExportService = Depends(get_export_service)
):
    """
    Exports a list of carbon credit retirement certificates.
    """
    target_company_id = company_id
    if current_user.role not in [UserRole.ADMIN, UserRole.AUDITOR]:
        if not current_user.company_id:
            raise PermissionDeniedException("User must belong to a company to export retirements")
        target_company_id = current_user.company_id

    from sqlalchemy.orm import joinedload
    stmt = select(Retirement).options(
        joinedload(Retirement.company),
        joinedload(Retirement.ownership).joinedload(Ownership.batch)
    )
    if target_company_id:
        stmt = stmt.where(Retirement.company_id == target_company_id)
        
    s_date = parse_date(start_date)
    e_date = parse_date(end_date)
    if s_date:
        stmt = stmt.where(Retirement.retired_at >= s_date)
    if e_date:
        stmt = stmt.where(Retirement.retired_at <= e_date)
        
    stmt = stmt.order_by(Retirement.retired_at.desc())
    retirements = db.execute(stmt).scalars().all()
    comp_name = db.query(Company.name).filter(Company.id == target_company_id).scalar() if target_company_id else "All Companies"

    headers = [
        "Certificate Number", "Company", "Batch Number", "Credits Retired",
        "Reason", "Verification Status", "Retired At"
    ]
    rows = []
    for ret in retirements:
        batch = ret.ownership.batch if ret.ownership else None
        rows.append([
            ret.certificate_number,
            ret.company.name if ret.company else "N/A",
            batch.batch_number if batch else "N/A",
            float(ret.credits_retired),
            ret.reason,
            "VERIFIED",
            ret.retired_at
        ])

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if format == "csv":
        data_bytes = exporter.export_to_csv(headers, rows)
        return Response(
            content=data_bytes,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=retirements_{timestamp}.csv"}
        )
    elif format == "excel":
        data_bytes = exporter.export_to_excel("Retirements", headers, rows, totals_cols=[3])
        return Response(
            content=data_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=retirements_{timestamp}.xlsx"}
        )
    else:
        data_bytes = exporter.export_to_pdf(
            f"Carbon Credit Retirements: {comp_name}",
            headers,
            rows,
            company_info={"name": comp_name, "id": str(target_company_id) if target_company_id else "Global"}
        )
        return Response(
            content=data_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=retirements_{timestamp}.pdf"}
        )


@router.get("/audit-logs")
def export_audit_logs(
    format: str = Query("csv", pattern="^(csv|excel|pdf)$"),
    user_id: Optional[uuid.UUID] = Query(None),
    action: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    exporter: ExportService = Depends(get_export_service)
):
    """
    Exports platform security and audit logs. Restricted to system administrators.
    """
    if current_user.role != UserRole.ADMIN:
        raise PermissionDeniedException("Audit log exports are restricted to system administrators")

    stmt = select(AuditLog)
    if user_id:
        stmt = stmt.where(AuditLog.user_id == user_id)
    if action:
        stmt = stmt.where(AuditLog.action == action)
        
    s_date = parse_date(start_date)
    e_date = parse_date(end_date)
    if s_date:
        stmt = stmt.where(AuditLog.timestamp >= s_date)
    if e_date:
        stmt = stmt.where(AuditLog.timestamp <= e_date)
        
    stmt = stmt.order_by(AuditLog.timestamp.desc())
    logs = db.execute(stmt).scalars().all()

    headers = [
        "Log ID", "User ID", "Company ID", "Entity Type", "Entity ID",
        "Action", "IP Address", "Timestamp"
    ]
    rows = []
    for log in logs:
        rows.append([
            str(log.id),
            str(log.user_id) if log.user_id else "N/A",
            str(log.company_id) if log.company_id else "N/A",
            log.entity_type,
            str(log.entity_id) if log.entity_id else "N/A",
            log.action,
            log.ip_address or "N/A",
            log.timestamp
        ])

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if format == "csv":
        data_bytes = exporter.export_to_csv(headers, rows)
        return Response(
            content=data_bytes,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=audit_logs_{timestamp}.csv"}
        )
    elif format == "excel":
        data_bytes = exporter.export_to_excel("Audit Logs", headers, rows, totals_cols=None)
        return Response(
            content=data_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=audit_logs_{timestamp}.xlsx"}
        )
    else:
        data_bytes = exporter.export_to_pdf(
            "System Administrative Audit Log Report",
            headers,
            rows,
            company_info={"name": "System Administration", "id": str(current_user.id)}
        )
        return Response(
            content=data_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=audit_logs_{timestamp}.pdf"}
        )
