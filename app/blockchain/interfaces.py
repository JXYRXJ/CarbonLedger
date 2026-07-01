import abc
from typing import Dict, Any, Optional


class IBlockchainService(abc.ABC):
    """
    Abstract interface for interacting with the CarbonLedger smart contract.
    """

    @abc.abstractmethod
    def register_batch(
        self,
        batch_id: str,
        project_id: str,
        total_credits: float,
        vintage_year: int,
        registry_id: str
    ) -> str:
        """
        Registers a carbon credit batch on the blockchain.
        Returns the transaction hash.
        """
        pass

    @abc.abstractmethod
    def record_transfer(
        self,
        transfer_id: str,
        batch_id: str,
        from_company: str,
        to_company: str,
        credits: float,
        transaction_hash_reference: str
    ) -> str:
        """
        Records a credit transfer ownership proof on-chain.
        Returns the transaction hash.
        """
        pass

    @abc.abstractmethod
    def record_retirement(
        self,
        retirement_id: str,
        batch_id: str,
        company_id: str,
        credits_retired: float,
        certificate_number: str
    ) -> str:
        """
        Records carbon credit retirement on-chain.
        Returns the transaction hash.
        """
        pass

    @abc.abstractmethod
    def record_audit(
        self,
        audit_id: str,
        entity_id: str,
        entity_type: str,
        action: str,
        performed_by: str
    ) -> str:
        """
        Records a secure system audit log checksum proof on-chain.
        Returns the transaction hash.
        """
        pass

    @abc.abstractmethod
    def verify_batch(self, batch_id: str) -> Dict[str, Any]:
        """
        Compares local DB batch state with on-chain record.
        Returns dictionary of comparison details.
        """
        pass

    @abc.abstractmethod
    def verify_transfer(self, transfer_id: str) -> Dict[str, Any]:
        """
        Compares transfer record between PostgreSQL and on-chain record.
        Returns comparison details.
        """
        pass

    @abc.abstractmethod
    def verify_retirement(self, retirement_id: str) -> Dict[str, Any]:
        """
        Compares credit retirement proof with on-chain state.
        """
        pass

    @abc.abstractmethod
    def verify_audit(self, audit_id: str) -> Dict[str, Any]:
        """
        Compares audit trail integrity.
        """
        pass

    @abc.abstractmethod
    def get_transaction_receipt(self, tx_hash: str) -> Dict[str, Any]:
        """
        Fetches detailed receipt for a transaction hash.
        """
        pass

    @abc.abstractmethod
    def get_block(self, block_number: int) -> Dict[str, Any]:
        """
        Fetches details of a block.
        """
        pass

    @abc.abstractmethod
    def estimate_gas(self, function_name: str, *args) -> int:
        """
        Estimates the gas required for a transaction.
        """
        pass

    @abc.abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """
        Returns connection and contract status details.
        """
        pass
