from typing import Any, Dict
from app.blockchain.client import BlockchainClient


class CarbonLedgerContractWrapper:
    """
    Contract-specific operations and properties.
    """

    def __init__(self, client: BlockchainClient) -> None:
        self.client = client

    @property
    def address(self) -> str:
        """Returns the checksummed address of the loaded smart contract."""
        if self.client and self.client.contract:
            return self.client.contract.address
        return ""

    @property
    def abi(self) -> list:
        """Returns the loaded contract ABI representation."""
        if self.client and self.client.contract:
            return self.client.contract.abi
        return []

    def get_role_member_count(self, role_hash: bytes) -> int:
        """Returns the number of members holding a role."""
        return self.client.call_read("getRoleMemberCount", role_hash)
