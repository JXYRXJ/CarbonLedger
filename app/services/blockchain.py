import abc
import uuid
from typing import Dict, Any, Optional


class IBlockchainOwnershipService(abc.ABC):
    """
    Interface definition for managing carbon asset ownership state on-chain.
    """

    @abc.abstractmethod
    def register_ownership(self, company_id: uuid.UUID, batch_id: uuid.UUID, credits: float) -> str:
        """
        Mints/registers carbon credit batch ownership records on-chain.
        Returns the transaction hash string.
        """
        pass

    @abc.abstractmethod
    def verify_ownership(self, company_id: uuid.UUID, batch_id: uuid.UUID) -> Dict[str, Any]:
        """
        Verifies on-chain credits ownership matching local DB ledger records.
        Returns verification details (on-chain balance, status, verified: bool).
        """
        pass

    @abc.abstractmethod
    def transfer_ownership(
        self,
        from_company_id: uuid.UUID,
        to_company_id: uuid.UUID,
        batch_id: uuid.UUID,
        credits: float
    ) -> str:
        """
        Executes on-chain ownership transfer between two companies.
        Returns transaction hash string.
        """
        pass


class IBlockchainRetirementService(abc.ABC):
    """
    Interface definition for recording carbon credit retirements permanently on-chain.
    """

    @abc.abstractmethod
    def record_retirement(
        self,
        retirement_id: uuid.UUID,
        company_id: uuid.UUID,
        credits: float,
        certificate_number: str
    ) -> str:
        """
        Records the retirement of credits permanently on-chain (burning/locking them).
        Returns transaction hash string.
        """
        pass


class IBlockchainAuditService(abc.ABC):
    """
    Interface definition for writing cryptographic hashes of system logs to the blockchain ledger.
    """

    @abc.abstractmethod
    def record_audit_log(
        self,
        audit_id: uuid.UUID,
        action: str,
        entity_type: str,
        entity_id: uuid.UUID,
        checksum: str
    ) -> str:
        """
        Records a cryptographic audit log state checksum on-chain for tamper-proofing.
        Returns transaction hash string.
        """
        pass


class IBlockchainEventProcessor(abc.ABC):
    """
    Interface definition for polling and processing inbound chain event logs.
    """

    @abc.abstractmethod
    def process_blockchain_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """
        Processes inbound chain events (reorgs, confirmations, contract triggers).
        """
        pass
