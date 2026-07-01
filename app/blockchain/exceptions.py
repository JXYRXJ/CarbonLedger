class BlockchainException(Exception):
    """Base exception for all blockchain/Web3 related errors."""
    pass


class BlockchainConnectionException(BlockchainException):
    """Raised when connecting to the blockchain node fails or disconnects."""
    pass


class ContractException(BlockchainException):
    """Raised when there is an issue loading or interacting with the smart contract."""
    pass


class TransactionFailedException(BlockchainException):
    """Raised when a sent blockchain transaction fails or reverts."""
    pass


class GasEstimationException(BlockchainException):
    """Raised when gas estimation for a transaction fails."""
    pass


class ConfirmationTimeoutException(BlockchainException):
    """Raised when waiting for a transaction confirmation times out."""
    pass


class NetworkMismatchException(BlockchainException):
    """Raised when the connected chain ID does not match the configured chain ID."""
    pass
