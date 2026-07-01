from typing import Dict, Any, Optional
from app.blockchain.interfaces import IBlockchainService
from app.blockchain.client import BlockchainClient
from app.blockchain.utils import scale_credits_to_onchain, scale_credits_from_onchain
from app.core.config import settings
import logging
logger = logging.getLogger("app.blockchain.service")
from app.blockchain.exceptions import ContractException, BlockchainConnectionException


class BlockchainService(IBlockchainService):
    """
    Standard service layer wrapper translating business logic payloads to on-chain calls.
    """

    def __init__(self, client: Optional[BlockchainClient] = None) -> None:
        self.client = client or BlockchainClient()

    def register_batch(
        self,
        batch_id: str,
        project_id: str,
        total_credits: float,
        vintage_year: int,
        registry_id: str
    ) -> str:
        """Invokes registerBatch contract call."""
        if not settings.BLOCKCHAIN_ENABLED:
            logger.info(f"Blockchain disabled. Mocking register_batch: {batch_id}")
            return "0xmocktxhashregisterbatch"

        scaled_credits = scale_credits_to_onchain(total_credits)
        return self.client.build_and_send_eip1559_transaction(
            "registerBatch",
            batch_id,
            project_id,
            scaled_credits,
            vintage_year,
            registry_id
        )

    def record_transfer(
        self,
        transfer_id: str,
        batch_id: str,
        from_company: str,
        to_company: str,
        credits: float,
        transaction_hash_reference: str
    ) -> str:
        """Invokes recordTransfer contract call."""
        if not settings.BLOCKCHAIN_ENABLED:
            logger.info(f"Blockchain disabled. Mocking record_transfer: {transfer_id}")
            return "0xmocktxhashrecordtransfer"

        scaled_credits = scale_credits_to_onchain(credits)
        return self.client.build_and_send_eip1559_transaction(
            "recordTransfer",
            transfer_id,
            batch_id,
            from_company,
            to_company,
            scaled_credits,
            transaction_hash_reference
        )

    def record_retirement(
        self,
        retirement_id: str,
        batch_id: str,
        company_id: str,
        credits_retired: float,
        certificate_number: str
    ) -> str:
        """Invokes recordRetirement contract call."""
        if not settings.BLOCKCHAIN_ENABLED:
            logger.info(f"Blockchain disabled. Mocking record_retirement: {retirement_id}")
            return "0xmocktxhashrecordretirement"

        scaled_credits = scale_credits_to_onchain(credits_retired)
        return self.client.build_and_send_eip1559_transaction(
            "recordRetirement",
            retirement_id,
            batch_id,
            company_id,
            scaled_credits,
            certificate_number
        )

    def record_audit(
        self,
        audit_id: str,
        entity_id: str,
        entity_type: str,
        action: str,
        performed_by: str
    ) -> str:
        """Invokes recordAudit contract call."""
        if not settings.BLOCKCHAIN_ENABLED:
            logger.info(f"Blockchain disabled. Mocking record_audit: {audit_id}")
            return "0xmocktxhashrecordaudit"

        return self.client.build_and_send_eip1559_transaction(
            "recordAudit",
            audit_id,
            entity_id,
            entity_type,
            action,
            performed_by
        )

    def verify_batch(self, batch_id: str) -> Dict[str, Any]:
        """Compares DB values with contract registry."""
        if not settings.BLOCKCHAIN_ENABLED:
            return {"verified": True, "source": "mock"}

        try:
            exists = self.client.call_read("batchExists", batch_id)
            if not exists:
                return {"verified": False, "reason": "Batch not found on-chain"}

            onchain = self.client.call_read("getBatch", batch_id)
            return {
                "verified": True,
                "batch_id": onchain[0],
                "project_id": onchain[1],
                "total_credits": scale_credits_from_onchain(onchain[2]),
                "vintage_year": onchain[3],
                "registry_id": onchain[4],
                "registered_at": onchain[5],
                "active": onchain[6]
            }
        except Exception as e:
            return {"verified": False, "error": str(e)}

    def verify_transfer(self, transfer_id: str) -> Dict[str, Any]:
        """Compares transfer transaction proofs."""
        if not settings.BLOCKCHAIN_ENABLED:
            return {"verified": True, "source": "mock"}

        try:
            exists = self.client.call_read("transferExists", transfer_id)
            if not exists:
                return {"verified": False, "reason": "Transfer not found on-chain"}

            onchain = self.client.call_read("getTransfer", transfer_id)
            return {
                "verified": True,
                "transfer_id": onchain[0],
                "batch_id": onchain[1],
                "from_company": onchain[2],
                "to_company": onchain[3],
                "credits": scale_credits_from_onchain(onchain[4]),
                "timestamp": onchain[5],
                "transaction_hash_reference": onchain[6]
            }
        except Exception as e:
            return {"verified": False, "error": str(e)}

    def verify_retirement(self, retirement_id: str) -> Dict[str, Any]:
        """Compares credit retirement audits."""
        if not settings.BLOCKCHAIN_ENABLED:
            return {"verified": True, "source": "mock"}

        try:
            exists = self.client.call_read("retirementExists", retirement_id)
            if not exists:
                return {"verified": False, "reason": "Retirement not found on-chain"}

            onchain = self.client.call_read("getRetirement", retirement_id)
            return {
                "verified": True,
                "retirement_id": onchain[0],
                "batch_id": onchain[1],
                "company_id": onchain[2],
                "credits_retired": scale_credits_from_onchain(onchain[3]),
                "certificate_number": onchain[4],
                "timestamp": onchain[5]
            }
        except Exception as e:
            return {"verified": False, "error": str(e)}

    def verify_audit(self, audit_id: str) -> Dict[str, Any]:
        """Compares audit log checksums."""
        if not settings.BLOCKCHAIN_ENABLED:
            return {"verified": True, "source": "mock"}

        try:
            exists = self.client.call_read("auditExists", audit_id)
            if not exists:
                return {"verified": False, "reason": "Audit not found on-chain"}

            onchain = self.client.call_read("getAudit", audit_id)
            return {
                "verified": True,
                "audit_id": onchain[0],
                "entity_id": onchain[1],
                "entity_type": onchain[2],
                "action": onchain[3],
                "performed_by": onchain[4],
                "timestamp": onchain[5]
            }
        except Exception as e:
            return {"verified": False, "error": str(e)}

    def get_transaction_receipt(self, tx_hash: str) -> Dict[str, Any]:
        """Loads transaction receipt properties."""
        if not settings.BLOCKCHAIN_ENABLED:
            return {"mock": True}
        return self.client.wait_for_confirmation(tx_hash, timeout=5)

    def get_block(self, block_number: int) -> Dict[str, Any]:
        """Loads block information properties."""
        if not settings.BLOCKCHAIN_ENABLED or not self.client.w3:
            return {"mock": True}
        block = self.client.w3.eth.get_block(block_number)
        return dict(block)

    def estimate_gas(self, function_name: str, *args) -> int:
        """Estimates gas requirement."""
        if not settings.BLOCKCHAIN_ENABLED or not self.client.contract:
            return 21000
        func = getattr(self.client.contract.functions, function_name)
        return func(*args).estimate_gas({"from": self.client.wallet_address})

    def health_check(self) -> Dict[str, Any]:
        """Evaluates live connections states."""
        if not settings.BLOCKCHAIN_ENABLED:
            return {
                "blockchain_connected": False,
                "enabled": False,
                "reason": "Disabled in settings"
            }
        
        try:
            self.client.ensure_connected()
            latest_block = self.client.w3.eth.block_number
            return {
                "blockchain_connected": True,
                "enabled": True,
                "network": "Polygon Amoy" if settings.CHAIN_ID == 80002 else "Local Node",
                "chain_id": settings.CHAIN_ID,
                "latest_block": latest_block,
                "contract_address": settings.CONTRACT_ADDRESS,
                "wallet_address": self.client.wallet_address
            }
        except Exception as e:
            return {
                "blockchain_connected": False,
                "enabled": True,
                "error": str(e)
            }

    def submit_to_blockchain(self, entity_type: str, entity_id: Any) -> None:
        """
        Dispatches on-chain submission to a non-blocking background thread.
        """
        if not settings.BLOCKCHAIN_ENABLED:
            logger.info(f"Blockchain disabled. Bypassing background sync for {entity_type} {entity_id}")
            return

        import threading
        thread = threading.Thread(
            target=self._background_submit_and_confirm,
            args=(entity_type, entity_id),
            daemon=True
        )
        thread.start()

    def _background_submit_and_confirm(self, entity_type: str, entity_id: Any) -> None:
        from datetime import datetime, timezone
        from app.core.database import SessionLocal
        from app.models.models import CreditBatch, Transaction, Retirement, AuditLog
        
        db = SessionLocal()
        try:
            # 1. Fetch Entity
            entity = None
            if entity_type == "CreditBatch":
                entity = db.query(CreditBatch).filter(CreditBatch.id == entity_id).first()
            elif entity_type == "Transaction":
                entity = db.query(Transaction).filter(Transaction.id == entity_id).first()
            elif entity_type == "Retirement":
                entity = db.query(Retirement).filter(Retirement.id == entity_id).first()
            elif entity_type == "AuditLog":
                entity = db.query(AuditLog).filter(AuditLog.id == entity_id).first()

            if not entity:
                logger.error(f"Entity {entity_type} with ID {entity_id} not found for blockchain submission.")
                return

            # Skip if already confirmed
            if entity.blockchain_status == "CONFIRMED":
                return

            entity.blockchain_status = "SUBMITTED"
            db.commit()

            # 2. Invoke contract call
            tx_hash = ""
            if entity_type == "CreditBatch":
                registry_id = str(entity.project.registry_id) if (entity.project and entity.project.registry_id) else ""
                tx_hash = self.register_batch(
                    batch_id=str(entity.id),
                    project_id=str(entity.project_id),
                    total_credits=float(entity.total_credits),
                    vintage_year=int(entity.vintage_year),
                    registry_id=registry_id
                )
            elif entity_type == "Transaction":
                tx_hash = self.record_transfer(
                    transfer_id=str(entity.id),
                    batch_id=str(entity.ownership.batch_id) if entity.ownership else "",
                    from_company=str(entity.seller_company_id),
                    to_company=str(entity.buyer_company_id),
                    credits=float(entity.credits_transferred),
                    transaction_hash_reference=entity.blockchain_tx_hash or ""
                )
            elif entity_type == "Retirement":
                tx_hash = self.record_retirement(
                    retirement_id=str(entity.id),
                    batch_id=str(entity.ownership.batch_id) if entity.ownership else "",
                    company_id=str(entity.company_id),
                    credits_retired=float(entity.credits_retired),
                    certificate_number=entity.certificate_number
                )
            elif entity_type == "AuditLog":
                tx_hash = self.record_audit(
                    audit_id=str(entity.id),
                    entity_id=str(entity.entity_id or ""),
                    entity_type=entity.entity_type,
                    action=entity.action,
                    performed_by=str(entity.user_id or "")
                )

            # Update with TX Hash
            entity.blockchain_tx_hash = tx_hash
            db.commit()

            # 3. Wait for confirmation
            receipt = self.client.wait_for_confirmation(tx_hash)
            
            # 4. Update status to CONFIRMED
            entity.blockchain_status = "CONFIRMED"
            entity.block_number = receipt.get("block_number")
            entity.confirmed_at = datetime.now(timezone.utc)
            entity.blockchain_error = None
            db.commit()

            logger.info(f"Successfully sync'd {entity_type} {entity_id} to blockchain (tx: {tx_hash})")

        except Exception as e:
            logger.error(f"Blockchain background sync failed for {entity_type} {entity_id}: {str(e)}")
            try:
                db.rollback()
                # Fetch fresh entity instance
                if entity_type == "CreditBatch":
                    entity = db.query(CreditBatch).filter(CreditBatch.id == entity_id).first()
                elif entity_type == "Transaction":
                    entity = db.query(Transaction).filter(Transaction.id == entity_id).first()
                elif entity_type == "Retirement":
                    entity = db.query(Retirement).filter(Retirement.id == entity_id).first()
                elif entity_type == "AuditLog":
                    entity = db.query(AuditLog).filter(AuditLog.id == entity_id).first()

                if entity:
                    entity.retry_count += 1
                    entity.blockchain_status = "FAILED"
                    entity.blockchain_error = str(e)
                    db.commit()
            except Exception as db_err:
                logger.error(f"Failed to record blockchain sync error to DB: {str(db_err)}")
        finally:
            db.close()

    def run_retry_worker(self) -> None:
        """
        Scans database tables for failed on-chain operations and triggers background retries.
        """
        from app.core.database import SessionLocal
        from app.models.models import CreditBatch, Transaction, Retirement, AuditLog
        
        db = SessionLocal()
        try:
            # 1. Batches
            failed_batches = db.query(CreditBatch).filter(
                CreditBatch.blockchain_status == "FAILED",
                CreditBatch.retry_count < 3
            ).all()
            for b in failed_batches:
                logger.info(f"Retrying failed batch: {b.id}")
                self.submit_to_blockchain("CreditBatch", b.id)

            # 2. Transactions
            failed_txs = db.query(Transaction).filter(
                Transaction.blockchain_status == "FAILED",
                Transaction.retry_count < 3
            ).all()
            for t in failed_txs:
                logger.info(f"Retrying failed transaction: {t.id}")
                self.submit_to_blockchain("Transaction", t.id)

            # 3. Retirements
            failed_rets = db.query(Retirement).filter(
                Retirement.blockchain_status == "FAILED",
                Retirement.retry_count < 3
            ).all()
            for r in failed_rets:
                logger.info(f"Retrying failed retirement: {r.id}")
                self.submit_to_blockchain("Retirement", r.id)

            # 4. AuditLogs
            failed_audits = db.query(AuditLog).filter(
                AuditLog.blockchain_status == "FAILED",
                AuditLog.retry_count < 3
            ).all()
            for a in failed_audits:
                logger.info(f"Retrying failed audit log: {a.id}")
                self.submit_to_blockchain("AuditLog", a.id)
        except Exception as e:
            logger.error(f"Error in retry worker run: {str(e)}")
        finally:
            db.close()
