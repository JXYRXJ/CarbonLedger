import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.models.models import User, UserRole, CreditBatch, Transaction, Retirement, AuditLog
from app.blockchain.client import BlockchainClient
from app.blockchain.service import BlockchainService
from app.blockchain.exceptions import (
    BlockchainConnectionException,
    ContractException,
    TransactionFailedException,
    GasEstimationException
)
from app.blockchain.utils import scale_credits_to_onchain, scale_credits_from_onchain


@pytest.fixture(autouse=True)
def configure_test_settings():
    """Forces settings to enable blockchain for the duration of the blockchain tests."""
    with patch.object(settings, "BLOCKCHAIN_ENABLED", True):
        with patch.object(settings, "PRIVATE_KEY", "0x" + "1" * 64):
            with patch.object(settings, "CONTRACT_ADDRESS", "0x" + "2" * 40):
                yield


@pytest.fixture
def mock_w3():
    with patch("app.blockchain.client.Web3") as mock:
        w3_instance = MagicMock()
        w3_instance.is_connected.return_value = True
        w3_instance.eth.chain_id = 1337
        w3_instance.eth.get_transaction_count.return_value = 5
        w3_instance.eth.gas_price = 1000000000
        w3_instance.eth.send_raw_transaction.return_value = b"mocktxhash"
        
        # EIP-1559 fee_history mockup returning int base fee and priority fee
        w3_instance.eth.fee_history.return_value = {
            "baseFeePerGas": [1000000000],
            "reward": [[2000000000]]
        }
        w3_instance.to_wei.return_value = 2000000000
        w3_instance.to_hex.return_value = "0x6d6f636b747868617368"
        w3_instance.to_checksum_address = lambda x: x
        
        w3_instance.eth.wait_for_transaction_receipt.return_value = {
            "status": 1,
            "blockNumber": 9999,
            "gasUsed": 50000,
            "effectiveGasPrice": 1000000000
        }
        mock.return_value = w3_instance
        yield w3_instance


@pytest.fixture
def mock_contract(mock_w3):
    contract_instance = MagicMock()
    # Mock return values for call() functions
    contract_instance.functions.batchExists.return_value.call.return_value = True
    contract_instance.functions.getBatch.return_value.call.return_value = (
        "batch-1", "proj-1", scale_credits_to_onchain(100.0), 2024, "reg-1", 1700000000, True
    )
    contract_instance.functions.transferExists.return_value.call.return_value = True
    contract_instance.functions.getTransfer.return_value.call.return_value = (
        "tx-1", "batch-1", "seller", "buyer", scale_credits_to_onchain(50.0), 1700000000, "db-ref"
    )
    contract_instance.functions.retirementExists.return_value.call.return_value = True
    contract_instance.functions.getRetirement.return_value.call.return_value = (
        "ret-1", "batch-1", "comp-1", scale_credits_to_onchain(20.0), "cert-1", 1700000000
    )
    contract_instance.functions.auditExists.return_value.call.return_value = True
    contract_instance.functions.getAudit.return_value.call.return_value = (
        "audit-1", "entity-1", "CreditBatch", "CREATE", "admin", 1700000000
    )
    
    mock_w3.eth.contract.return_value = contract_instance
    yield contract_instance


def test_credits_scaling():
    assert scale_credits_to_onchain(1.5) == 1500000000000000000
    assert scale_credits_from_onchain(1500000000000000000) == 1.5


def test_blockchain_client_connection(mock_w3, mock_contract):
    with patch("builtins.open", create=True):
        with patch("json.load", return_value=[{"inputs": []}]):
            client = BlockchainClient()
            assert client.w3 is not None
            assert client.contract is not None
            client.ensure_connected()


def test_blockchain_service_reads(mock_w3, mock_contract):
    with patch("builtins.open", create=True):
        with patch("json.load", return_value=[]):
            client = BlockchainClient()
            service = BlockchainService(client)
            
            # Verify batch read
            res = service.verify_batch("batch-1")
            assert res["verified"] is True
            assert res["total_credits"] == 100.0
            
            # Verify transfer read
            res = service.verify_transfer("tx-1")
            assert res["verified"] is True
            assert res["credits"] == 50.0

            # Verify retirement read
            res = service.verify_retirement("ret-1")
            assert res["verified"] is True
            assert res["credits_retired"] == 20.0


def test_blockchain_service_writes(mock_w3, mock_contract):
    with patch("builtins.open", create=True):
        with patch("json.load", return_value=[]):
            client = BlockchainClient()
            service = BlockchainService(client)

            # Test EIP-1559 tx build and sign
            tx_hash = service.register_batch("batch-1", "proj-1", 100.0, 2024, "reg-1")
            assert tx_hash == "0x6d6f636b747868617368"
            
            tx_hash = service.record_transfer("tx-1", "batch-1", "seller", "buyer", 50.0, "ref")
            assert tx_hash == "0x6d6f636b747868617368"


def test_admin_blockchain_health(client, auth_headers):
    from app.core.database import SessionLocal
    db = SessionLocal()
    admin_id = uuid.uuid4()
    try:
        admin_user = User(
            id=admin_id,
            first_name="Admin",
            last_name="User",
            email=f"admin_{admin_id.hex}@example.com",
            hashed_password="hashed",
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin_user)
        db.commit()
    finally:
        db.close()

    headers = auth_headers(sub=str(admin_id), role="ADMIN")
    resp = client.get("/api/v1/admin/blockchain/health", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    assert "blockchain_connected" in resp.json()["data"]


def test_admin_blockchain_status(client, auth_headers):
    from app.core.database import SessionLocal
    db = SessionLocal()
    admin_id = uuid.uuid4()
    try:
        admin_user = User(
            id=admin_id,
            first_name="Admin",
            last_name="User",
            email=f"admin_{admin_id.hex}@example.com",
            hashed_password="hashed",
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin_user)
        
        # Create temp database batch
        batch = CreditBatch(
            id=uuid.uuid4(),
            project_id=uuid.uuid4(),
            batch_number=f"TEST-BATCH-RETRY-{uuid.uuid4().hex[:6].upper()}",
            vintage_year=2024,
            total_credits=5000,
            remaining_credits=5000,
            issuance_date=datetime.now().date(),
            blockchain_status="FAILED",
            retry_count=0
        )
        db.add(batch)
        db.commit()
    finally:
        db.close()

    headers = auth_headers(sub=str(admin_id), role="ADMIN")
    resp = client.get("/api/v1/admin/blockchain/status", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    assert "batches" in resp.json()["data"]
    assert resp.json()["data"]["batches"]["failed"] >= 1


def test_admin_blockchain_retry(client, auth_headers):
    from app.core.database import SessionLocal
    db = SessionLocal()
    admin_id = uuid.uuid4()
    try:
        admin_user = User(
            id=admin_id,
            first_name="Admin",
            last_name="User",
            email=f"admin_{admin_id.hex}@example.com",
            hashed_password="hashed",
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin_user)

        batch = CreditBatch(
            id=uuid.uuid4(),
            project_id=uuid.uuid4(),
            batch_number=f"TEST-BATCH-RETRY-{uuid.uuid4().hex[:6].upper()}",
            vintage_year=2024,
            total_credits=5000,
            remaining_credits=5000,
            issuance_date=datetime.now().date(),
            blockchain_status="FAILED",
            retry_count=1
        )
        db.add(batch)
        db.commit()
        batch_id = batch.id
    finally:
        db.close()

    # Stub the blockchain register_batch to bypass active node connections
    with patch("app.blockchain.service.BlockchainService.register_batch", return_value="0xmanualretrytxhash"):
        headers = auth_headers(sub=str(admin_id), role="ADMIN")
        resp = client.post(f"/api/v1/admin/blockchain/retry/{batch_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        assert resp.json()["data"]["tx_hash"] == "0xmanualretrytxhash"

        # Check DB updated state
        db = SessionLocal()
        try:
            batch = db.query(CreditBatch).filter(CreditBatch.id == batch_id).first()
            assert batch.blockchain_status == "SUBMITTED"
            assert batch.blockchain_tx_hash == "0xmanualretrytxhash"
            assert batch.blockchain_error is None
        finally:
            db.close()
