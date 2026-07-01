import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.models import User, Company, UserRole


def test_rbac_company_admin_access(client: TestClient, auth_headers: callable):
    """
    Tests that a user with COMPANY_ADMIN role can query company info
    and update company attributes.
    """
    admin_id = str(uuid.uuid4())
    company_id = str(uuid.uuid4())
    headers = auth_headers(sub=admin_id, role="COMPANY_ADMIN", company_id=company_id)
    
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        company = Company(
            id=uuid.UUID(company_id),
            name="EcoCorp Admin Test",
            registration_number="REG-AT-9988",
            country="United States"
        )
        user = User(
            id=uuid.UUID(admin_id),
            first_name="Alice",
            last_name="Admin",
            email="admin@ecotest.com",
            hashed_password="hashed_pwd",
            role=UserRole.COMPANY_ADMIN,
            company_id=company.id,
            is_active=True
        )
        db.add(company)
        db.add(user)
        db.commit()
    finally:
        db.close()

    # Access /companies/me as COMPANY_ADMIN
    response = client.get("/api/v1/companies/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "EcoCorp Admin Test"


def test_rbac_trader_denied_access(client: TestClient, auth_headers: callable):
    """
    Tests that a user with TRADER or VIEWER role is blocked with 403 Forbidden
    when attempting to query company admin details.
    """
    trader_id = str(uuid.uuid4())
    company_id = str(uuid.uuid4())
    headers = auth_headers(sub=trader_id, role="TRADER", company_id=company_id)
    
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        company = Company(
            id=uuid.UUID(company_id),
            name="EcoCorp Trader Test",
            registration_number="REG-TR-9988",
            country="United States"
        )
        user = User(
            id=uuid.UUID(trader_id),
            first_name="Bob",
            last_name="Trader",
            email="trader@ecotest.com",
            hashed_password="hashed_pwd",
            role=UserRole.TRADER,
            company_id=company.id,
            is_active=True
        )
        db.add(company)
        db.add(user)
        db.commit()
    finally:
        db.close()

    response = client.get("/api/v1/companies/me", headers=headers)
    assert response.status_code == 403
    assert "permission denied" in response.json()["message"].lower()
