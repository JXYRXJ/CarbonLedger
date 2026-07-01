import pytest
import uuid
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.models import Registry, CarbonProject, CreditBatch, User, UserRole, Company, Ownership, Retirement, MarketplaceListing, PurchaseOrder, Transaction


def test_analytics_metrics_and_permissions(client: TestClient, db_session: Session, auth_headers: callable):
    """
    Verifies that dashboard, marketplace, and portfolio analytics endpoints return accurate
    aggregations and respect access control permissions.
    """
    company_id = uuid.uuid4()
    company = Company(id=company_id, name="Energy Corp", registration_number="EN-123", country="US")
    db_session.add(company)

    user_id = uuid.uuid4()
    user = User(
        id=user_id, first_name="Bob", last_name="Trader", email="bob@energycorp.com",
        hashed_password="hashed_password", role=UserRole.TRADER, company_id=company_id, is_active=True
    )
    db_session.add(user)

    reg_id = uuid.uuid4()
    proj_id = uuid.uuid4()
    batch_id = uuid.uuid4()
    ownership_id = uuid.uuid4()

    reg = Registry(id=reg_id, name="Verra Registry", country="US", website="https://verra.org", accreditation="ANSI")
    p = CarbonProject(
        id=proj_id, registry_id=reg_id, project_code="VCS-111", name="Solar Project", country="US",
        project_type="Solar", verification_standard="VCS", methodology="AM0001", developer="SolarDev",
        start_date=date(2020, 1, 1), end_date=date(2030, 12, 31)
    )
    batch = CreditBatch(
        id=batch_id, project_id=proj_id, batch_number="VCS-SOLAR-2024", vintage_year=2024,
        total_credits=10000.0, remaining_credits=10000.0, issuance_date=date(2024, 6, 1)
    )
    ownership = Ownership(
        id=ownership_id, company_id=company_id, batch_id=batch_id, owned_credits=5000.0, average_purchase_price=10.00
    )

    db_session.add(reg)
    db_session.add(p)
    db_session.add(batch)
    db_session.add(ownership)
    db_session.commit()

    # Create a completed transaction to build marketplace volume
    tx_id = uuid.uuid4()
    order_id = uuid.uuid4()
    tx = Transaction(
        id=tx_id, order_id=order_id, buyer_company_id=company_id, seller_company_id=uuid.uuid4(),
        ownership_id=ownership_id, credits_transferred=500.0, price_per_credit=10.00, total_price=5000.00,
        status="COMPLETED"
    )
    db_session.add(tx)
    db_session.commit()

    # Create a retirement record
    ret_id = uuid.uuid4()
    ret = Retirement(
        id=ret_id, ownership_id=ownership_id, company_id=company_id, credits_retired=200.0,
        reason="Offset", certificate_number="CL-CERT-111-2024"
    )
    db_session.add(ret)
    db_session.commit()

    headers = auth_headers(sub=str(user_id), role="TRADER", company_id=str(company_id))

    # 1. Test Dashboard Analytics
    resp = client.get("/api/v1/analytics/dashboard", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["credits_available"] == 5000.0
    assert resp.json()["data"]["credits_retired"] == 200.0
    assert resp.json()["data"]["completed_transactions"] == 1

    # 2. Test Marketplace Analytics
    mp_resp = client.get("/api/v1/analytics/marketplace", headers=headers)
    assert mp_resp.status_code == 200
    assert mp_resp.json()["data"]["most_active_registry"] == "Verra Registry"
    assert mp_resp.json()["data"]["most_active_project"] == "Solar Project"

    # 3. Test Portfolio Analytics
    pf_resp = client.get("/api/v1/analytics/portfolio", headers=headers)
    assert pf_resp.status_code == 200
    assert pf_resp.json()["data"]["credits_owned"] == 5000.0
    assert pf_resp.json()["data"]["credits_retired"] == 200.0
    assert pf_resp.json()["data"]["estimated_portfolio_value"] == 50000.0
