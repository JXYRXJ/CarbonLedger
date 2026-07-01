import uuid
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, select

from app.core.database import get_db
from app.core.config import settings
from app.core.exceptions import PermissionDeniedException, NotFoundException, BusinessRuleException
from app.core.dependencies import get_current_active_user
from app.models.models import User, UserRole, CreditBatch, Transaction, Retirement, AuditLog
from app.schemas.responses import APIResponse
from app.blockchain.service import BlockchainService

router = APIRouter(prefix="/admin/blockchain", tags=["Admin Blockchain Operations"])


def get_blockchain_service() -> BlockchainService:
    return BlockchainService()


@router.get("/health", response_model=APIResponse[dict])
def get_blockchain_health(
    current_user: User = Depends(get_current_active_user),
    service: BlockchainService = Depends(get_blockchain_service)
):
    """
    Exposes detailed blockchain network connection, chain ID, block numbers, contract, and wallet info.
    Permissions: ADMIN only.
    """
    if current_user.role != UserRole.ADMIN:
        raise PermissionDeniedException("Only administrators can view blockchain health")

    return APIResponse(
        success=True,
        message="Blockchain health retrieved successfully",
        data=service.health_check()
    )


@router.get("/status", response_model=APIResponse[dict])
def get_blockchain_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Returns aggregation stats of blockchain synchronization states.
    Permissions: ADMIN only.
    """
    if current_user.role != UserRole.ADMIN:
        raise PermissionDeniedException("Only administrators can view blockchain status")

    # Counts by status in batches
    batches_pending = db.query(CreditBatch).filter(CreditBatch.blockchain_status == "PENDING").count()
    batches_confirmed = db.query(CreditBatch).filter(CreditBatch.blockchain_status == "CONFIRMED").count()
    batches_failed = db.query(CreditBatch).filter(CreditBatch.blockchain_status == "FAILED").count()

    # Counts in transactions
    tx_pending = db.query(Transaction).filter(Transaction.blockchain_status == "PENDING").count()
    tx_confirmed = db.query(Transaction).filter(Transaction.blockchain_status == "CONFIRMED").count()
    tx_failed = db.query(Transaction).filter(Transaction.blockchain_status == "FAILED").count()

    # Counts in retirements
    ret_pending = db.query(Retirement).filter(Retirement.blockchain_status == "PENDING").count()
    ret_confirmed = db.query(Retirement).filter(Retirement.blockchain_status == "CONFIRMED").count()
    ret_failed = db.query(Retirement).filter(Retirement.blockchain_status == "FAILED").count()

    return APIResponse(
        success=True,
        message="Blockchain status aggregation completed",
        data={
            "batches": {"pending": batches_pending, "confirmed": batches_confirmed, "failed": batches_failed},
            "transactions": {"pending": tx_pending, "confirmed": tx_confirmed, "failed": tx_failed},
            "retirements": {"pending": ret_pending, "confirmed": ret_confirmed, "failed": ret_failed}
        }
    )


@router.get("/transactions", response_model=APIResponse[list])
def get_blockchain_transactions(
    status: Optional[str] = Query(None, regex="^(PENDING|SUBMITTED|CONFIRMED|FAILED|RETRYING)$"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Lists transaction sync items matching optional status filters.
    Permissions: ADMIN only.
    """
    if current_user.role != UserRole.ADMIN:
        raise PermissionDeniedException("Only administrators can view blockchain transactions list")

    results = []

    # 1. Fetch Batches
    batches_query = db.query(CreditBatch)
    if status:
        batches_query = batches_query.filter(CreditBatch.blockchain_status == status)
    for b in batches_query.limit(50).all():
        results.append({
            "operation_id": str(b.id),
            "type": "BATCH_REGISTRATION",
            "identifier": b.batch_number,
            "status": b.blockchain_status,
            "tx_hash": b.blockchain_tx_hash,
            "retry_count": b.retry_count,
            "error": b.blockchain_error
        })

    # 2. Fetch Transactions
    tx_query = db.query(Transaction)
    if status:
        tx_query = tx_query.filter(Transaction.blockchain_status == status)
    for t in tx_query.limit(50).all():
        results.append({
            "operation_id": str(t.id),
            "type": "OWNERSHIP_TRANSFER",
            "identifier": str(t.id),
            "status": t.blockchain_status,
            "tx_hash": t.blockchain_tx_hash,
            "retry_count": t.retry_count,
            "error": t.blockchain_error
        })

    # 3. Fetch Retirements
    ret_query = db.query(Retirement)
    if status:
        ret_query = ret_query.filter(Retirement.blockchain_status == status)
    for r in ret_query.limit(50).all():
        results.append({
            "operation_id": str(r.id),
            "type": "CREDITS_RETIREMENT",
            "identifier": r.certificate_number,
            "status": r.blockchain_status,
            "tx_hash": r.blockchain_tx_hash,
            "retry_count": r.retry_count,
            "error": r.blockchain_error
        })

    return APIResponse(
        success=True,
        message="Blockchain transactions loaded",
        data=results
    )


@router.post("/retry/{operation_id}", response_model=APIResponse[dict])
def retry_blockchain_operation(
    operation_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    service: BlockchainService = Depends(get_blockchain_service)
):
    """
    Manually retries a failed on-chain synchronization operation for an entity.
    Permissions: ADMIN only.
    """
    if current_user.role != UserRole.ADMIN:
        raise PermissionDeniedException("Only administrators can trigger blockchain retries")

    # 1. Check Batches
    batch = db.query(CreditBatch).filter(CreditBatch.id == operation_id).first()
    if batch:
        try:
            tx_hash = service.register_batch(
                batch_id=str(batch.id),
                project_id=str(batch.project_id),
                total_credits=float(batch.total_credits),
                vintage_year=int(batch.vintage_year),
                registry_id=str(batch.project.registry_id) if batch.project else ""
            )
            batch.blockchain_status = "SUBMITTED"
            batch.blockchain_tx_hash = tx_hash
            batch.blockchain_error = None
            db.commit()
            return APIResponse(
                success=True,
                message="Retried batch registration successfully submitted",
                data={"tx_hash": tx_hash}
            )
        except Exception as e:
            batch.retry_count += 1
            batch.blockchain_status = "FAILED"
            batch.blockchain_error = str(e)
            db.commit()
            raise BusinessRuleException(f"Retry execution failed: {str(e)}")

    # 2. Check Transactions
    tx = db.query(Transaction).filter(Transaction.id == operation_id).first()
    if tx:
        try:
            tx_hash = service.record_transfer(
                transfer_id=str(tx.id),
                batch_id=str(tx.ownership.batch_id) if tx.ownership else "",
                from_company=str(tx.seller_company_id),
                to_company=str(tx.buyer_company_id),
                credits=float(tx.credits_transferred),
                transaction_hash_reference=tx.blockchain_tx_hash or ""
            )
            tx.blockchain_status = "SUBMITTED"
            tx.blockchain_tx_hash = tx_hash
            tx.blockchain_error = None
            db.commit()
            return APIResponse(
                success=True,
                message="Retried ownership transfer successfully submitted",
                data={"tx_hash": tx_hash}
            )
        except Exception as e:
            tx.retry_count += 1
            tx.blockchain_status = "FAILED"
            tx.blockchain_error = str(e)
            db.commit()
            raise BusinessRuleException(f"Retry execution failed: {str(e)}")

    # 3. Check Retirements
    ret = db.query(Retirement).filter(Retirement.id == operation_id).first()
    if ret:
        try:
            tx_hash = service.record_retirement(
                retirement_id=str(ret.id),
                batch_id=str(ret.ownership.batch_id) if ret.ownership else "",
                company_id=str(ret.company_id),
                credits_retired=float(ret.credits_retired),
                certificate_number=ret.certificate_number
            )
            ret.blockchain_status = "SUBMITTED"
            ret.blockchain_tx_hash = tx_hash
            ret.blockchain_error = None
            db.commit()
            return APIResponse(
                success=True,
                message="Retried retirement successfully submitted",
                data={"tx_hash": tx_hash}
            )
        except Exception as e:
            ret.retry_count += 1
            ret.blockchain_status = "FAILED"
            ret.blockchain_error = str(e)
            db.commit()
            raise BusinessRuleException(f"Retry execution failed: {str(e)}")

    raise NotFoundException(f"No blockchain operational record found for ID: {operation_id}")
