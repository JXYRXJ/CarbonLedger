import pytest
import uuid
from datetime import date, datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.models import Registry, CarbonProject, CreditBatch, User, UserRole, BatchStatus


def test_create_credit_batch_validations(client: TestClient, db_session: Session, auth_headers: callable):
    """
    Tests registering a new credit batch. Validates uniqueness of batch number,
    admin checks, and vintage year rules.
    """
    admin_id = uuid.uuid4()
    admin_user = User(
        id=admin_id,
        first_name="Admin",
        last_name="User",
        email="admin-batch@carbonledger.com",
        hashed_password="hashed_password",
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(admin_user)
    
    # Seed registry and project
    reg_id = uuid.uuid4()
    proj_id = uuid.uuid4()
    
    reg = Registry(id=reg_id, name="Batch Reg", country="US", website="https://verra.org", accreditation="ANSI")
    p = CarbonProject(
        id=proj_id,
        registry_id=reg_id,
        project_code="VCS-BATCH-01",
        name="Batch Project",
        country="US",
        project_type="Forestry",
        verification_standard="VCS",
        methodology="VM0007",
        developer="GreenDev",
        start_date=date(2020, 1, 1),
        end_date=date(2030, 12, 31)
    )
    db_session.add(reg)
    db_session.add(p)
    db_session.commit()

    headers = auth_headers(sub=str(admin_id), role="ADMIN")

    # 1. Success Create
    payload = {
        "project_id": str(proj_id),
        "batch_number": "BATCH-2024-001",
        "vintage_year": 2024,
        "total_credits": 10000.0,
        "remaining_credits": 10000.0,
        "issuance_date": "2024-06-01",
        "metadata_json": {"verification_auditor": "SGS"}
    }
    resp = client.post("/api/v1/batches", json=payload, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["data"]["batch_number"] == "BATCH-2024-001"

    # 2. Reject duplicate batch number
    dup_resp = client.post("/api/v1/batches", json=payload, headers=headers)
    assert dup_resp.status_code == 409

    # 3. Reject future vintage year
    future_payload = payload.copy()
    future_payload["batch_number"] = "BATCH-FUTURE"
    future_payload["vintage_year"] = datetime.now().year + 1
    
    future_resp = client.post("/api/v1/batches", json=future_payload, headers=headers)
    assert future_resp.status_code == 422


def test_batch_status_transitions(client: TestClient, db_session: Session, auth_headers: callable):
    """
    Verifies that credit batch status transitions are validated
    and terminal statuses (like RETIRED) cannot go back to ACTIVE.
    """
    admin_id = uuid.uuid4()
    admin_user = User(
        id=admin_id,
        first_name="Admin",
        last_name="User",
        email="admin-status@carbonledger.com",
        hashed_password="hashed_password",
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(admin_user)

    reg_id = uuid.uuid4()
    proj_id = uuid.uuid4()
    batch_id = uuid.uuid4()
    
    reg = Registry(id=reg_id, name="Transition Reg", country="US", website="https://verra.org", accreditation="ANSI")
    p = CarbonProject(
        id=proj_id, registry_id=reg_id, project_code="VCS-T-01", name="Proj", country="US",
        project_type="Forestry", verification_standard="VCS", methodology="VM0007", developer="Dev",
        start_date=date(2020, 1, 1), end_date=date(2030, 12, 31)
    )
    batch = CreditBatch(
        id=batch_id,
        project_id=proj_id,
        batch_number="BATCH-T-001",
        vintage_year=2024,
        total_credits=5000.0,
        remaining_credits=5000.0,
        issuance_date=date(2024, 6, 1),
        status=BatchStatus.ACTIVE
    )
    db_session.add(reg)
    db_session.add(p)
    db_session.add(batch)
    db_session.commit()

    headers = auth_headers(sub=str(admin_id), role="ADMIN")

    # 1. Update status to RETIRED (Valid)
    resp = client.patch(f"/api/v1/batches/{batch_id}", json={"status": "RETIRED"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "RETIRED"

    # 2. Transition from RETIRED back to ACTIVE (Blocked)
    blocked_resp = client.patch(f"/api/v1/batches/{batch_id}", json={"status": "ACTIVE"}, headers=headers)
    assert blocked_resp.status_code == 400
    assert "terminal status" in blocked_resp.json()["message"].lower()
