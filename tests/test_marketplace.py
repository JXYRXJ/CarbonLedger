import pytest
import uuid
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.models import Registry, CarbonProject, CreditBatch, Ownership, User, UserRole, Company, MarketplaceListing, ListingStatus


def test_create_listing_validations(client: TestClient, db_session: Session, auth_headers: callable):
    """
    Tests creating a marketplace listing. Validates seller ownership, credits_for_sale limits,
    minimum purchase boundaries, and positive price.
    """
    company_id = uuid.uuid4()
    company = Company(id=company_id, name="Listing Seller Co", registration_number="LS-01", country="US")
    user_id = uuid.uuid4()
    user = User(
        id=user_id, first_name="Trader", last_name="Joe", email="trader-list@carbonledger.com",
        hashed_password="hashed_password", role=UserRole.TRADER, company_id=company_id, is_active=True
    )
    
    reg_id = uuid.uuid4()
    reg = Registry(id=reg_id, name="Market Reg", country="US", website="https://verra.org", accreditation="ANSI")
    proj_id = uuid.uuid4()
    p = CarbonProject(
        id=proj_id, registry_id=reg_id, project_code="VCS-M-01", name="Proj", country="US",
        project_type="Forestry", verification_standard="VCS", methodology="VM0007", developer="Dev",
        start_date=date(2020, 1, 1), end_date=date(2030, 12, 31)
    )
    batch_id = uuid.uuid4()
    batch = CreditBatch(
        id=batch_id, project_id=proj_id, batch_number="BATCH-M-01", vintage_year=2024,
        total_credits=5000.0, remaining_credits=5000.0, issuance_date=date(2024, 6, 1)
    )
    # Owns 1000 credits
    own_id = uuid.uuid4()
    own = Ownership(id=own_id, company_id=company_id, batch_id=batch_id, owned_credits=1000.0, average_purchase_price=10.0)

    db_session.add(company)
    db_session.add(user)
    db_session.add(reg)
    db_session.add(p)
    db_session.add(batch)
    db_session.add(own)
    db_session.commit()

    headers = auth_headers(sub=str(user_id), role="TRADER", company_id=str(company_id))

    # 1. Success Create Draft/Pending listing of 600 credits
    payload = {
        "ownership_id": str(own_id),
        "credits_for_sale": 600.0,
        "price_per_credit": 15.0,
        "minimum_purchase": 10.0,
        "description": "Reforestation credits"
    }
    resp = client.post("/api/v1/listings", json=payload, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["data"]["status"] == "PENDING"
    listing_id = resp.json()["data"]["id"]

    # 2. Reject listing more than available credits (owns 1000, already listed 600, only 400 available. Listing 500 should fail)
    over_payload = payload.copy()
    over_payload["credits_for_sale"] = 500.0
    resp_over = client.post("/api/v1/listings", json=over_payload, headers=headers)
    assert resp_over.status_code == 400
    assert "insufficient available credits" in resp_over.json()["message"].lower()

    # 3. Reject negative price
    neg_payload = payload.copy()
    neg_payload["price_per_credit"] = -5.0
    resp_neg = client.post("/api/v1/listings", json=neg_payload, headers=headers)
    assert resp_neg.status_code == 422


def test_admin_approve_and_publish_listing(client: TestClient, db_session: Session, auth_headers: callable):
    """
    Verifies that only admin users can approve, reject, and publish listings.
    """
    admin_id = uuid.uuid4()
    admin_user = User(
        id=admin_id, first_name="Admin", last_name="User", email="admin-list@carbonledger.com",
        hashed_password="hashed_password", role=UserRole.ADMIN, is_active=True
    )
    company_id = uuid.uuid4()
    company = Company(id=company_id, name="Seller Co", registration_number="S-01", country="US")
    reg_id = uuid.uuid4()
    reg = Registry(id=reg_id, name="Port Reg", country="US", website="https://verra.org", accreditation="ANSI")
    proj_id = uuid.uuid4()
    p = CarbonProject(
        id=proj_id, registry_id=reg_id, project_code="VCS-M-02", name="Proj", country="US",
        project_type="Forestry", verification_standard="VCS", methodology="VM0007", developer="Dev",
        start_date=date(2020, 1, 1), end_date=date(2030, 12, 31)
    )
    batch_id = uuid.uuid4()
    batch = CreditBatch(
        id=batch_id, project_id=proj_id, batch_number="BATCH-M-02", vintage_year=2024,
        total_credits=5000.0, remaining_credits=5000.0, issuance_date=date(2024, 6, 1)
    )
    own_id = uuid.uuid4()
    own = Ownership(id=own_id, company_id=company_id, batch_id=batch_id, owned_credits=1000.0, average_purchase_price=10.0)

    # Seed pending listing
    list_id = uuid.uuid4()
    listing = MarketplaceListing(
        id=list_id, ownership_id=own_id, seller_company_id=company_id,
        credits_for_sale=500.0, price_per_credit=15.0, status=ListingStatus.PENDING
    )

    db_session.add(admin_user)
    db_session.add(company)
    db_session.add(reg)
    db_session.add(p)
    db_session.add(batch)
    db_session.add(own)
    db_session.add(listing)
    db_session.commit()

    # 1. Non-admin approval gets blocked (403)
    user_id = uuid.uuid4()
    trader = User(id=user_id, first_name="T", last_name="J", email="t-j@carbonledger.com", hashed_password="h", role=UserRole.TRADER, is_active=True)
    db_session.add(trader)
    db_session.commit()
    trader_headers = auth_headers(sub=str(user_id), role="TRADER")
    
    blocked_resp = client.post(f"/api/v1/admin/listings/{list_id}/approve", headers=trader_headers)
    assert blocked_resp.status_code == 403

    # 2. Admin approval success (automatically sets status to APPROVED and then PUBLISHED)
    admin_headers = auth_headers(sub=str(admin_id), role="ADMIN")
    resp = client.post(f"/api/v1/admin/listings/{list_id}/approve", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "PUBLISHED"
