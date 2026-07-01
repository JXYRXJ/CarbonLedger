import pytest
import uuid
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.models import Registry, CarbonProject, CreditBatch, Ownership, MarketplaceListing, ListingStatus, User, UserRole, Company


def test_dynamic_portfolio_aggregates_and_locks(client: TestClient, db_session: Session, auth_headers: callable):
    """
    Seeds a company owning 1000 credits, with 300 of those credits listed in the marketplace.
    Verifies that portfolio statistics correctly compute:
    - total owned credits = 1000
    - listed credits = 300
    - available credits = 700
    - estimated portfolio book value based on average purchase price.
    """
    company_id = uuid.uuid4()
    company = Company(
        id=company_id,
        name="Dynamic Portfolio Co",
        registration_number="DP-01",
        wallet_address="0x71C7656EC7ab88b098defB751B7401B5f6d8976F",
        country="US"
    )
    
    # Seed user for authentication
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        first_name="Trader",
        last_name="One",
        email="trader-port@carbonledger.com",
        hashed_password="password_hash",
        role=UserRole.TRADER,
        company_id=company_id,
        is_active=True
    )

    reg_id = uuid.uuid4()
    reg = Registry(id=reg_id, name="Port Reg", country="US", website="https://verra.org", accreditation="ANSI")
    proj_id = uuid.uuid4()
    p = CarbonProject(
        id=proj_id, registry_id=reg_id, project_code="VCS-P-01", name="Proj", country="US",
        project_type="Forestry", verification_standard="VCS", methodology="VM0007", developer="Dev",
        start_date=date(2020, 1, 1), end_date=date(2030, 12, 31)
    )
    batch_id = uuid.uuid4()
    batch = CreditBatch(
        id=batch_id, project_id=proj_id, batch_number="BATCH-PORT-01", vintage_year=2024,
        total_credits=2000.0, remaining_credits=2000.0, issuance_date=date(2024, 6, 1)
    )
    
    # Ownership: 1000 credits at an average purchase price of $12.50/credit (Portfolio Value = 1000 * 12.5 = $12500)
    own_id = uuid.uuid4()
    own = Ownership(
        id=own_id,
        company_id=company_id,
        batch_id=batch_id,
        owned_credits=1000.0,
        average_purchase_price=12.50
    )
    
    # Listing: 300 credits listed for sale on the marketplace (uses seller_company_id)
    listing = MarketplaceListing(
        id=uuid.uuid4(),
        ownership_id=own_id,
        seller_company_id=company_id,
        credits_for_sale=300.0,
        price_per_credit=15.0,
        status=ListingStatus.PUBLISHED
    )

    db_session.add(company)
    db_session.add(user)
    db_session.add(reg)
    db_session.add(p)
    db_session.add(batch)
    db_session.add(own)
    db_session.add(listing)
    db_session.commit()

    headers = auth_headers(sub=str(user_id), role="TRADER", company_id=str(company_id))

    # 1. Fetch entire /portfolio summary endpoint
    resp = client.get("/api/v1/portfolio", headers=headers)
    assert resp.status_code == 200
    
    data = resp.json()["data"]
    assert data["company"]["name"] == "Dynamic Portfolio Co"
    
    summary = data["portfolio_summary"]
    assert summary["owned_credit_count"] == 1000.0
    assert summary["listed_credit_count"] == 300.0
    assert summary["available_credit_count"] == 700.0
    assert summary["estimated_portfolio_value"] == 12500.0

    # 2. Fetch /portfolio/statistics
    stats_resp = client.get("/api/v1/portfolio/statistics", headers=headers)
    assert stats_resp.status_code == 200
    assert stats_resp.json()["data"]["available_credit_count"] == 700.0

    # 3. Fetch /portfolio/batches
    batches_resp = client.get("/api/v1/portfolio/batches", headers=headers)
    assert batches_resp.status_code == 200
    assert len(batches_resp.json()["data"]) == 1
    assert batches_resp.json()["data"][0]["available_credits"] == 700.0
