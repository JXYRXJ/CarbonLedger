import time
from typing import Dict, Any, List
from sqlalchemy.orm import Session
import logging
logger = logging.getLogger("app.blockchain.listeners")
from app.blockchain.client import BlockchainClient
from app.blockchain.events import parse_contract_events


class BlockchainEventListener:
    """
    Syncs and validates smart contract events with local database models.
    """

    def __init__(self, client: BlockchainClient) -> None:
        self.client = client

    def sync_and_verify_events(self, db: Session, event_name: str, block_number: int) -> int:
        """
        Retrieves logs for a given event name at a specific block number,
        and verifies their integrity against database records.
        """
        if not self.client.contract or not self.client.w3:
            logger.warning("Blockchain client is not loaded. Skipping verification.")
            return 0

        try:
            event_obj = getattr(self.client.contract.events, event_name)
            logs = event_obj().get_logs(fromBlock=block_number, toBlock=block_number)
            
            mismatches = 0
            for log in logs:
                tx_hash = log["transactionHash"].hex()
                args = log["args"]
                
                # Verify based on event type
                if event_name == "BatchRegistered":
                    batch_id = args.get("batchId")
                    from app.models.models import CreditBatch
                    batch = db.query(CreditBatch).filter(CreditBatch.id == batch_id).first()
                    if not batch:
                        logger.error(f"[LOG MISMATCH] Batch {batch_id} registered on-chain in tx {tx_hash} but not found in DB!")
                        mismatches += 1
                        
                elif event_name == "OwnershipTransferred":
                    transfer_id = args.get("transferId")
                    from app.models.models import Transaction
                    tx = db.query(Transaction).filter(Transaction.id == transfer_id).first()
                    if not tx:
                        logger.error(f"[LOG MISMATCH] Transaction {transfer_id} transferred on-chain in tx {tx_hash} but not found in DB!")
                        mismatches += 1
                        
                elif event_name == "CreditsRetired":
                    retirement_id = args.get("retirementId")
                    from app.models.models import Retirement
                    ret = db.query(Retirement).filter(Retirement.id == retirement_id).first()
                    if not ret:
                        logger.error(f"[LOG MISMATCH] Retirement {retirement_id} recorded on-chain in tx {tx_hash} but not found in DB!")
                        mismatches += 1
                        
                elif event_name == "AuditRecorded":
                    audit_id = args.get("auditId")
                    from app.models.models import AuditLog
                    audit = db.query(AuditLog).filter(AuditLog.id == audit_id).first()
                    if not audit:
                        logger.error(f"[LOG MISMATCH] Audit log {audit_id} written on-chain in tx {tx_hash} but not found in DB!")
                        mismatches += 1

            return mismatches
        except Exception as e:
            logger.error(f"Error during event synchronization verify: {str(e)}")
            return 0
