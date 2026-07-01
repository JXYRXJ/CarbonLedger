import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import PermissionDeniedException
from app.core.dependencies import get_current_active_user
from app.models.models import User, UserRole
from app.schemas.responses import APIResponse
from app.services.services import TransactionService
from app.repositories.repositories import TransactionRepository

router = APIRouter()


def get_transaction_service(db: Session = Depends(get_db)) -> TransactionService:
    return TransactionService(TransactionRepository(db))


@router.get("/transactions", response_model=APIResponse[list])
def list_transactions(
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    service: TransactionService = Depends(get_transaction_service)
):
    """
    List transactions.
    Auditors and Admins can view all transactions.
    Corporate users can view transactions where their company is the buyer or seller.
    """
    if current_user.role in [UserRole.ADMIN, UserRole.AUDITOR]:
        if search:
            txs = service.search_transactions(search)
        else:
            txs = service.list_transactions()
    else:
        if not current_user.company_id:
            raise PermissionDeniedException("User has no associated company")
        txs = service.list_transactions(company_id=current_user.company_id)

    data = []
    for tx in txs:
        purchase_order = tx.purchase_order
        listing = purchase_order.listing if purchase_order else None
        ownership = tx.ownership
        batch = ownership.batch if ownership else None
        project = batch.project if batch else None
        registry = project.registry if project else None

        data.append({
            "id": str(tx.id),
            "order_id": str(tx.order_id),
            "buyer": {
                "id": str(tx.buyer_company_id),
                "name": tx.buyer_company.name if tx.buyer_company else None
            },
            "seller": {
                "id": str(tx.seller_company_id),
                "name": tx.seller_company.name if tx.seller_company else None
            },
            "batch": {
                "id": str(batch.id) if batch else None,
                "batch_number": batch.batch_number if batch else None
            } if batch else None,
            "project": {
                "id": str(project.id) if project else None,
                "name": project.name if project else None,
                "project_code": project.project_code if project else None
            } if project else None,
            "registry": {
                "id": str(registry.id) if registry else None,
                "name": registry.name if registry else None
            } if registry else None,
            "credits_transferred": float(tx.credits_transferred),
            "price_per_credit": float(tx.price_per_credit),
            "total_price": float(tx.total_price),
            "status": tx.status,
            "completed_at": tx.completed_at.isoformat() if tx.completed_at else None,
            "blockchain_tx_hash": tx.blockchain_tx_hash
        })

    return {
        "success": True,
        "message": "Transactions retrieved successfully",
        "data": data
    }


@router.get("/transactions/{transaction_id}", response_model=APIResponse[dict])
def get_transaction_details(
    transaction_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    service: TransactionService = Depends(get_transaction_service)
):
    """
    Retrieve details of a specific transaction.
    Permissions: Admin, Auditor, or Buyer/Seller company users.
    """
    tx = service.get_transaction(transaction_id)
    
    if current_user.role not in [UserRole.ADMIN, UserRole.AUDITOR]:
        if current_user.company_id not in [tx.buyer_company_id, tx.seller_company_id]:
            raise PermissionDeniedException("You do not have permission to view this transaction")

    purchase_order = tx.purchase_order
    ownership = tx.ownership
    batch = ownership.batch if ownership else None
    project = batch.project if batch else None
    registry = project.registry if project else None

    return {
        "success": True,
        "message": "Transaction details retrieved successfully",
        "data": {
            "id": str(tx.id),
            "order_id": str(tx.order_id),
            "buyer": {
                "id": str(tx.buyer_company_id),
                "name": tx.buyer_company.name if tx.buyer_company else None
            },
            "seller": {
                "id": str(tx.seller_company_id),
                "name": tx.seller_company.name if tx.seller_company else None
            },
            "batch": {
                "id": str(batch.id) if batch else None,
                "batch_number": batch.batch_number if batch else None
            } if batch else None,
            "project": {
                "id": str(project.id) if project else None,
                "name": project.name if project else None,
                "project_code": project.project_code if project else None
            } if project else None,
            "registry": {
                "id": str(registry.id) if registry else None,
                "name": registry.name if registry else None
            } if registry else None,
            "credits_transferred": float(tx.credits_transferred),
            "price_per_credit": float(tx.price_per_credit),
            "total_price": float(tx.total_price),
            "status": tx.status,
            "completed_at": tx.completed_at.isoformat() if tx.completed_at else None,
            "blockchain_tx_hash": tx.blockchain_tx_hash
        }
    }
