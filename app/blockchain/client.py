import json
import os
from typing import Dict, Any, Optional
from web3 import Web3
try:
    from web3.middleware import ExtraDataToPOAMiddleware as geth_poa_middleware
except ImportError:
    try:
        from web3.middleware.geth_poa import geth_poa_middleware
    except ImportError:
        from web3.middleware import geth_poa_middleware
from eth_account import Account

from app.core.config import settings
import logging
logger = logging.getLogger("app.blockchain")
from app.blockchain.exceptions import (
    BlockchainConnectionException,
    ContractException,
    TransactionFailedException,
    GasEstimationException,
    ConfirmationTimeoutException,
    NetworkMismatchException
)
from app.blockchain.utils import clean_private_key, is_valid_ethereum_address


class BlockchainClient:
    """
    Wrapper for Web3 connectivity, contract loading, transaction building, signing, and state lookups.
    """

    def __init__(self) -> None:
        self.w3: Optional[Web3] = None
        self.contract: Optional[Any] = None
        self.wallet_address: Optional[str] = None
        self.private_key: Optional[str] = None

        if settings.BLOCKCHAIN_ENABLED:
            self.connect()

    def connect(self) -> None:
        """Establishes or reconnects Web3 provider connection and loads the smart contract."""
        try:
            logger.info("Initializing Web3 connection to provider...")
            
            # 1. Setup HTTP connection
            self.w3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER_URL))
            
            # Inject Geth PoA middleware for testnets (like Amoy)
            self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

            # 2. Check connection
            if not self.w3.is_connected():
                raise BlockchainConnectionException(
                    f"Failed to connect to blockchain node at {settings.WEB3_PROVIDER_URL}"
                )

            # 3. Network Validation
            chain_id = self.w3.eth.chain_id
            if chain_id != settings.CHAIN_ID:
                raise NetworkMismatchException(
                    f"Connected chain ID ({chain_id}) does not match configured chain ID ({settings.CHAIN_ID})"
                )

            # 4. Load wallet if private key is supplied
            if settings.PRIVATE_KEY:
                cleaned_key = clean_private_key(settings.PRIVATE_KEY)
                self.private_key = cleaned_key
                account = Account.from_key(cleaned_key)
                self.wallet_address = account.address
                logger.info(f"Loaded blockchain wallet address: {self.wallet_address}")
            else:
                self.wallet_address = settings.WALLET_ADDRESS
                logger.warning("No private key supplied. Transactions requiring signing will fail.")

            # 5. Load Smart Contract
            self._load_contract()
            logger.info("Successfully established connection to blockchain node.")

        except Exception as e:
            logger.error(f"Blockchain Client connection error: {str(e)}")
            self.w3 = None
            self.contract = None
            if not settings.is_testing:
                raise BlockchainConnectionException(f"Node connection failed: {str(e)}")

    def _load_contract(self) -> None:
        """Loads contract ABI and initializes contract instance."""
        if not self.w3:
            raise BlockchainConnectionException("Web3 client is not initialized")

        if not is_valid_ethereum_address(settings.CONTRACT_ADDRESS):
            raise ContractException(f"Invalid contract address format: {settings.CONTRACT_ADDRESS}")

        abi_path = os.path.join(os.path.dirname(__file__), "abis", "CarbonLedger.json")
        try:
            with open(abi_path, "r") as f:
                abi = json.load(f)
            
            checksum_address = self.w3.to_checksum_address(settings.CONTRACT_ADDRESS)
            self.contract = self.w3.eth.contract(address=checksum_address, abi=abi)
            logger.info(f"Loaded CarbonLedger smart contract at checksum address: {checksum_address}")
        except FileNotFoundError:
            raise ContractException(f"Contract ABI file not found at path: {abi_path}")
        except Exception as e:
            raise ContractException(f"Error loading smart contract: {str(e)}")

    def ensure_connected(self) -> None:
        """Checks connection state and attempts reconnection if disconnected."""
        if not self.w3 or not self.w3.is_connected():
            logger.warning("Blockchain node connection lost. Reconnecting...")
            self.connect()
            if not self.w3 or not self.w3.is_connected():
                raise BlockchainConnectionException("Failed to reconnect to blockchain node")

    def call_read(self, function_name: str, *args) -> Any:
        """Executes a read-only smart contract function call."""
        self.ensure_connected()
        if not self.contract:
            raise ContractException("Smart contract is not loaded")

        try:
            func = getattr(self.contract.functions, function_name)
            return func(*args).call()
        except Exception as e:
            logger.error(f"Error executing contract read {function_name}: {str(e)}")
            raise ContractException(f"Read operation failed: {str(e)}")

    def build_and_send_eip1559_transaction(self, function_name: str, *args) -> str:
        """Builds, signs, and dispatches an EIP-1559 transaction to the blockchain."""
        self.ensure_connected()
        if not self.contract:
            raise ContractException("Smart contract is not loaded")
        if not self.private_key or not self.wallet_address:
            raise ContractException("Wallet private key is not configured for signing transactions")

        try:
            # 1. Fetch Nonce
            nonce = self.w3.eth.get_transaction_count(self.wallet_address, "pending")

            # 2. Estimate Fees
            try:
                history = self.w3.eth.fee_history(1, "latest", [50.0])
                base_fee = history["baseFeePerGas"][-1]
                priority_fee = history["reward"][0][0]
                max_fee = (base_fee * 2) + priority_fee
            except Exception:
                # Fallback to gas price + priority tip
                gas_price = self.w3.eth.gas_price
                priority_fee = self.w3.to_wei(2, "gwei")
                max_fee = gas_price + priority_fee

            # Bound by max configured gas price
            if max_fee > settings.MAX_GAS_PRICE:
                max_fee = settings.MAX_GAS_PRICE

            # 3. Get contract method
            func = getattr(self.contract.functions, function_name)
            
            # 4. Estimate Gas
            try:
                gas_estimate = func(*args).estimate_gas({"from": self.wallet_address})
                # Add 20% safety buffer
                gas_limit = int(gas_estimate * 1.2)
            except Exception as ge:
                logger.warning(f"Gas estimation failed, falling back to config limit. Error: {str(ge)}")
                gas_limit = settings.GAS_LIMIT

            # 5. Build Transaction Dict
            tx_dict = func(*args).build_transaction({
                "chainId": settings.CHAIN_ID,
                "from": self.wallet_address,
                "nonce": nonce,
                "gas": gas_limit,
                "maxFeePerGas": max_fee,
                "maxPriorityFeePerGas": priority_fee
            })

            # 6. Sign and Send
            signed_tx = self.w3.eth.account.sign_transaction(tx_dict, self.private_key)
            logger.info(f"Submitting transaction {function_name} with nonce {nonce}...")
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            return self.w3.to_hex(tx_hash)

        except Exception as e:
            logger.error(f"Error submitting transaction {function_name}: {str(e)}")
            raise TransactionFailedException(f"Transaction build/send failed: {str(e)}")

    def wait_for_confirmation(self, tx_hash: str, timeout: int = 120) -> Dict[str, Any]:
        """Waits for receipt confirmations of a submitted transaction."""
        self.ensure_connected()
        try:
            logger.info(f"Waiting for transaction confirmation: {tx_hash}...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout, poll_latency=1)
            
            # Check execution status
            if receipt["status"] != 1:
                raise TransactionFailedException(f"Transaction execution reverted on-chain: {tx_hash}")

            logger.info(f"Transaction confirmed in block {receipt['blockNumber']}! Gas used: {receipt['gasUsed']}")
            return {
                "tx_hash": tx_hash,
                "block_number": receipt["blockNumber"],
                "gas_used": receipt["gasUsed"],
                "effective_gas_price": receipt.get("effectiveGasPrice", 0),
                "status": "CONFIRMED"
            }
        except TimeoutError:
            raise ConfirmationTimeoutException(f"Timeout waiting for transaction confirmation: {tx_hash}")
        except Exception as e:
            logger.error(f"Error checking transaction receipt {tx_hash}: {str(e)}")
            raise TransactionFailedException(f"Transaction receipt retrieval failed: {str(e)}")
