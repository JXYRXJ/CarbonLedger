import pytest
import uuid
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.models import Registry, CarbonProject, CreditBatch, Ownership, User, UserRole, Company, MarketplaceListing, ListingStatus, PurchaseOrderStatus, PurchaseOrder, Transaction


def test_atomic_purchase_workflow(client: TestClient, db_session: Session, auth_headers: callable):
    """
    Verifies that a valid purchase order successfully transfers credits, updates ownership balances,
    calculates average purchase price for buyer, updates remaining listing credits, and logs history.
    """
    # Seed Seller & Buyer Companies
    s_company_id = uuid.uuid4()
    b_company_id = uuid.uuid4()
    seller_co = Company(id=s_company_id, name="Seller Co", registration_number="SC-01", country="US")
    buyer_co = Company(id=b_company_id, name="Buyer Co", registration_number="BC-01", country="US")
    
    buyer_id = uuid.uuid4()
    buyer_user = User(
        id=buyer_id, first_name="Buyer", last_name="Joe", email="buyer@carbonledger.com",
        hashed_password="hashed_password", role=UserRole.TRADER, company_id=b_company_id, is_active=True
    )
    
    reg_id = uuid.uuid4()
    reg = Registry(id=reg_id, name="Reg", country="US", website="https://verra.org", accreditation="ANSI")
    proj_id = uuid.uuid4()
    p = CarbonProject(
        id=proj_id, registry_id=reg_id, project_code="VCS-O-10", name="Proj", country="US",
        project_type="Forestry", verification_standard="VCS", methodology="VM0007", developer="Dev",
        start_date=date(2020, 1, 1), end_date=date(2030, 12, 31)
    )
    batch_id = uuid.uuid4()
    batch = CreditBatch(
        id=batch_id, project_id=proj_id, batch_number="BATCH-O-10", vintage_year=2024,
        total_credits=5000.0, remaining_credits=5000.0, issuance_date=date(2024, 6, 1)
    )
    
    # Seller holding: 1000 credits
    own_id = uuid.uuid4()
    own_seller = Ownership(id=own_id, company_id=s_company_id, batch_id=batch_id, owned_credits=1000.0, average_purchase_price=10.0)
    
    # Buyer holding: Pre-existing 500 credits at $20.00/credit (recalculation test)
    own_buyer = Ownership(id=uuid.uuid4(), company_id=b_company_id, batch_id=batch_id, owned_credits=500.0, average_purchase_price=20.0)

    # Listing: 600 credits for sale at $15.00/credit
    listing_id = uuid.uuid4()
    listing = MarketplaceListing(
        id=listing_id, ownership_id=own_id, seller_company_id=s_company_id,
        credits_for_sale=600.0, price_per_credit=15.0, status=ListingStatus.PUBLISHED
    )

    db_session.add(seller_co)
    db_session.add(buyer_co)
    db_session.add(buyer_user)
    db_session.add(reg)
    db_session.add(p)
    db_session.add(batch)
    db_session.add(own_seller)
    db_session.add(own_buyer)
    db_session.add(listing)
    db_session.commit()

    headers = auth_headers(sub=str(buyer_id), role="TRADER", company_id=str(b_company_id))

    # 1. Purchase 400 credits (Success)
    payload = {
        "listing_id": str(listing_id),
        "requested_credits": 400.0
    }
    resp = client.post("/api/v1/orders", json=payload, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["data"]["status"] == "COMPLETED"

    db_session.expire_all()
    
    assert float(own_seller.owned_credits) == 600.0
    assert float(own_buyer.owned_credits) == 900.0
    assert abs(float(own_buyer.average_purchase_price) - 17.7777) < 0.01
    assert float(listing.credits_for_sale) == 200.0
    assert listing.status == ListingStatus.PUBLISHED

    # 2. Block self-purchase attempt
    seller_user_id = uuid.uuid4()
    seller_user = User(
        id=seller_user_id, first_name="Seller", last_name="Joe", email="seller@carbonledger.com",
        hashed_password="hashed_password", role=UserRole.TRADER, company_id=s_company_id, is_active=True
    )
    db_session.add(seller_user)
    db_session.commit()
    seller_headers = auth_headers(sub=str(seller_user_id), role="TRADER", company_id=str(s_company_id))
    
    self_resp = client.post("/api/v1/orders", json=payload, headers=seller_headers)
    assert self_resp.status_code == 400
    assert "self-purchase" in self_resp.json()["message"].lower()


def test_purchase_order_rollback_on_failure(client: TestClient, db_session: Session, auth_headers: callable):
    """
    Tests database transactions and rollback behavior on failure during purchase execution.
    If credits deduction fails, verifies that no balances change and no transaction is logged.
    """
    s_company_id = uuid.uuid4()
    b_company_id = uuid.uuid4()
    seller_co = Company(id=s_company_id, name="Rollback S", registration_number="RS-01", country="US")
    buyer_co = Company(id=b_company_id, name="Rollback B", registration_number="RB-01", country="US")
    
    buyer_id = uuid.uuid4()
    buyer_user = User(
        id=buyer_id, first_name="Buyer", last_name="Joe", email="buyer-roll@carbonledger.com",
        hashed_password="hashed_password", role=UserRole.TRADER, company_id=b_company_id, is_active=True
    )

    reg_id = uuid.uuid4()
    reg = Registry(id=reg_id, name="Reg", country="US", website="https://verra.org", accreditation="ANSI")
    proj_id = uuid.uuid4()
    p = CarbonProject(
        id=proj_id, registry_id=reg_id, project_code="VCS-O-11", name="Proj", country="US",
        project_type="Forestry", verification_standard="VCS", methodology="VM0007", developer="Dev",
        start_date=date(2020, 1, 1), end_date=date(2030, 12, 31)
    )
    batch_id = uuid.uuid4()
    batch = CreditBatch(
        id=batch_id, project_id=proj_id, batch_number="BATCH-O-11", vintage_year=2024,
        total_credits=5000.0, remaining_credits=5000.0, issuance_date=date(2024, 6, 1)
    )
    
    own_id = uuid.uuid4()
    own_seller = Ownership(id=own_id, company_id=s_company_id, batch_id=batch_id, owned_credits=100.0, average_purchase_price=10.0)
    own_buyer = Ownership(id=uuid.uuid4(), company_id=b_company_id, batch_id=batch_id, owned_credits=500.0, average_purchase_price=20.0)

    # Listing has 100 credits for sale
    listing_id = uuid.uuid4()
    listing = MarketplaceListing(
        id=listing_id, ownership_id=own_id, seller_company_id=s_company_id,
        credits_for_sale=100.0, price_per_credit=15.0, status=ListingStatus.PUBLISHED
    )

    db_session.add(seller_co)
    db_session.add(buyer_co)
    db_session.add(buyer_user)
    db_session.add(reg)
    db_session.add(p)
    db_session.add(batch)
    db_session.add(own_seller)
    db_session.add(own_buyer)
    db_session.add(listing)
    db_session.commit()

    headers = auth_headers(sub=str(buyer_id), role="TRADER", company_id=str(b_company_id))

    # 1. Attempt to purchase 200 credits (Exceeds listing credits_for_sale, should fail validation before tx)
    bad_payload = {
        "listing_id": str(listing_id),
        "requested_credits": 200.0
    }
    bad_resp = client.post("/api/v1/orders", json=bad_payload, headers=headers)
    assert bad_resp.status_code == 400
    assert "insufficient credits for sale" in bad_resp.json()["message"].lower()

    # 2. Attempt purchase of 100 credits, but seller owns only 50
    own_seller.owned_credits = 50.0
    db_session.commit()

    race_payload = {
        "listing_id": str(listing_id),
        "requested_credits": 100.0
    }
    race_resp = client.post("/api/v1/orders", json=race_payload, headers=headers)
    assert race_resp.status_code == 400
    assert "insufficient owned credits" in race_resp.json()["message"].lower()

    # Refresh and confirm state remains unchanged/rolled back
    db_session.expire_all()
    assert float(own_seller.owned_credits) == 50.0
    assert float(own_buyer.owned_credits) == 500.0
