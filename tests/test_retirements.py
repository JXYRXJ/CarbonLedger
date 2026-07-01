import pytest
import uuid
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.models import Registry, CarbonProject, CreditBatch, User, UserRole, Company, Ownership, Retirement


def test_retirement_workflow_and_validations(client: TestClient, db_session: Session, auth_headers: callable):
    """
    Verifies the complete carbon credit retirement workflow, certificate generation,
    insufficient credits checks, and RBAC / scope restrictions.
    """
    company_id = uuid.uuid4()
    company = Company(
        id=company_id,
        name="Retire Corp",
        registration_number="RE-12345",
        country="US"
    )
    db_session.add(company)

    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        first_name="Alice",
        last_name="Trader",
        email="alice@retirecorp.com",
        hashed_password="hashed_password",
        role=UserRole.TRADER,
        company_id=company_id,
        is_active=True
    )
    db_session.add(user)

    reg_id = uuid.uuid4()
    proj_id = uuid.uuid4()
    batch_id = uuid.uuid4()
    ownership_id = uuid.uuid4()

    reg = Registry(id=reg_id, name="Gold Standard", country="CH", website="https://goldstandard.org", accreditation="ANSI")
    p = CarbonProject(
        id=proj_id, registry_id=reg_id, project_code="GS-999", name="Wind Power Proj", country="IN",
        project_type="Wind", verification_standard="GS", methodology="ACM0002", developer="CleanGen",
        start_date=date(2020, 1, 1), end_date=date(2030, 12, 31)
    )
    batch = CreditBatch(
        id=batch_id, project_id=proj_id, batch_number="GS-WIND-2024", vintage_year=2024,
        total_credits=5000.0, remaining_credits=5000.0, issuance_date=date(2024, 6, 1)
    )
    ownership = Ownership(
        id=ownership_id, company_id=company_id, batch_id=batch_id, owned_credits=1000.0, average_purchase_price=12.50
    )

    db_session.add(reg)
    db_session.add(p)
    db_session.add(batch)
    db_session.add(ownership)
    db_session.commit()

    headers = auth_headers(sub=str(user_id), role="TRADER", company_id=str(company_id))

    # 1. Success Retirement
    payload = {
        "ownership_id": str(ownership_id),
        "quantity": 300.0,
        "beneficiary_name": "Retire Corp Offset",
        "retirement_reason": "Scope 2 Emissions Reduction"
    }
    resp = client.post("/api/v1/retirements", json=payload, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["success"] is True
    assert "CL-CERT" in resp.json()["data"]["certificate_number"]
    assert resp.json()["data"]["credits_retired"] == 300.0
    retirement_id = resp.json()["data"]["id"]

    # Verify database state
    db_session.refresh(ownership)
    assert float(ownership.owned_credits) == 700.0

    # 2. Insufficient Credits check
    fail_payload = {
        "ownership_id": str(ownership_id),
        "quantity": 800.0,
        "beneficiary_name": "Too Big",
        "retirement_reason": "Exceeding Balance"
    }
    fail_resp = client.post("/api/v1/retirements", json=fail_payload, headers=headers)
    assert fail_resp.status_code == 400
    assert "insufficient" in fail_resp.json()["message"].lower()

    # 3. Get retirement detail
    detail_resp = client.get(f"/api/v1/retirements/{retirement_id}", headers=headers)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["data"]["credits_retired"] == 300.0

    # 4. Get certificate view metadata
    cert_resp = client.get(f"/api/v1/retirements/{retirement_id}/certificate", headers=headers)
    assert cert_resp.status_code == 200
    assert cert_resp.json()["data"]["company"]["name"] == "Retire Corp"
    assert cert_resp.json()["data"]["project"]["project_code"] == "GS-999"

    # 5. Access control: Unauthorized other company user tries to retrieve certificate
    other_company_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    other_user = User(
        id=other_user_id, first_name="Bob", last_name="Trader", email="bob@other.com",
        hashed_password="hashed_password", role=UserRole.TRADER, company_id=other_company_id, is_active=True
    )
    db_session.add(other_user)
    db_session.commit()

    other_headers = auth_headers(sub=str(other_user_id), role="TRADER", company_id=str(other_company_id))
    unauth_resp = client.get(f"/api/v1/retirements/{retirement_id}/certificate", headers=other_headers)
    assert unauth_resp.status_code == 403
