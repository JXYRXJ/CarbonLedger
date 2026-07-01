import threading
from typing import Dict, Any, Tuple
from web3 import Web3
from app.core.config import settings
from app.core.logging import logger


class NonceManager:
    """
    Thread-safe nonce manager to prevent race conditions during concurrent transaction submissions.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._nonces: Dict[str, int] = {}

    def get_and_increment_nonce(self, w3: Web3, wallet_address: str) -> int:
        """Atomically retrieves the current nonce and increments it."""
        with self._lock:
            # Sync with the network pending count
            network_nonce = w3.eth.get_transaction_count(wallet_address, "pending")
            stored_nonce = self._nonces.get(wallet_address, 0)
            
            # Use whichever is higher to avoid nonce reuses
            nonce = max(network_nonce, stored_nonce)
            self._nonces[wallet_address] = nonce + 1
            return nonce

    def reset_nonce(self, wallet_address: str) -> None:
        """Resets stored nonce force-syncing with network on next get."""
        with self._lock:
            if wallet_address in self._nonces:
                del self._nonces[wallet_address]


nonce_manager = NonceManager()


def calculate_eip1559_fees(w3: Web3) -> Tuple[int, int]:
    """
    Calculates EIP-1559 gas fees dynamically using block fee history.
    Returns: (max_fee_per_gas, max_priority_fee_per_gas)
    """
    try:
        # Fetch history for the latest block
        history = w3.eth.fee_history(1, "latest", [50.0])
        base_fee = history["baseFeePerGas"][-1]
        priority_fee = history["reward"][0][0]
        
        # Max fee = (base_fee * 2) + priority_fee (standard buffer for block changes)
        max_fee = (base_fee * 2) + priority_fee
        return max_fee, priority_fee
    except Exception as e:
        logger.warning(f"Error calculating EIP-1559 fees, falling back to standard gas prices. Error: {str(e)}")
        gas_price = w3.eth.gas_price
        priority_fee = w3.to_wei(2, "gwei")
        max_fee = gas_price + priority_fee
        return max_fee, priority_fee
