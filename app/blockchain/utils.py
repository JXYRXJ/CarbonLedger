import re
from typing import Union
from web3 import Web3

# Decimals precision to represent float credits as uint256 on-chain
CREDIT_DECIMALS = 18
CREDIT_SCALE = 10 ** CREDIT_DECIMALS


def is_valid_ethereum_address(address: str) -> bool:
    """Verifies if a string is a valid Ethereum hex address format."""
    if not address or not isinstance(address, str):
        return False
    return Web3.is_address(address)


def clean_private_key(key: str) -> str:
    """Ensures private key does not contain 0x prefix."""
    if not key:
        return ""
    key = key.strip()
    if key.startswith("0x") or key.startswith("0X"):
        return key[2:]
    return key


def scale_credits_to_onchain(credits: Union[int, float]) -> int:
    """Converts local decimal float credits to on-chain uint256 representation (18 decimals)."""
    return int(float(credits) * CREDIT_SCALE)


def scale_credits_from_onchain(credits_uint: int) -> float:
    """Converts on-chain uint256 representation back to float credits."""
    return float(credits_uint) / CREDIT_SCALE
