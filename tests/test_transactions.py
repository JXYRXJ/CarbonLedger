import pytest
import uuid
from datetime import date, datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.models import Registry, CarbonProject, CreditBatch, Ownership, User, UserRole, Company, MarketplaceListing, ListingStatus, PurchaseOrderStatus, PurchaseOrder, Transaction


def test_transaction_visibility_and_search(client: TestClient, db_session: Session, auth_headers: callable):
    """
    Tests visibility permissions for completed transactions:
    - Admins and Auditors can view all transactions and search by company keyword.
    - Company traders can only see transactions where their company is either buyer or seller.
    """
    # Seed Company A, B, and C
    cA_id = uuid.uuid4()
    cB_id = uuid.uuid4()
    cC_id = uuid.uuid4()
    
    co_A = Company(id=cA_id, name="Company Alpha", registration_number="CA-01", country="US")
    co_B = Company(id=cB_id, name="Company Beta", registration_number="CB-01", country="US")
    co_C = Company(id=cC_id, name="Company Gamma", registration_number="CC-01", country="US")

    user_A = User(
        id=uuid.uuid4(), first_name="Trader", last_name="A", email="trader-a@carbonledger.com",
        hashed_password="hashed_password", role=UserRole.TRADER, company_id=cA_id, is_active=True
    )
    user_B = User(
        id=uuid.uuid4(), first_name="Trader", last_name="B", email="trader-b@carbonledger.com",
        hashed_password="hashed_password", role=UserRole.TRADER, company_id=cB_id, is_active=True
    )

    reg_id = uuid.uuid4()
    reg = Registry(id=reg_id, name="Reg", country="US", website="https://verra.org", accreditation="ANSI")
    proj_id = uuid.uuid4()
    p = CarbonProject(
        id=proj_id, registry_id=reg_id, project_code="VCS-TX-01", name="Proj", country="US",
        project_type="Forestry", verification_standard="VCS", methodology="VM0007", developer="Dev",
        start_date=date(2020, 1, 1), end_date=date(2030, 12, 31)
    )
    batch_id = uuid.uuid4()
    batch = CreditBatch(
        id=batch_id, project_id=proj_id, batch_number="BATCH-TX-01", vintage_year=2024,
        total_credits=5000.0, remaining_credits=5000.0, issuance_date=date(2024, 6, 1)
    )
    
    own_A = Ownership(id=uuid.uuid4(), company_id=cA_id, batch_id=batch_id, owned_credits=100.0, average_purchase_price=10.0)
    own_B = Ownership(id=uuid.uuid4(), company_id=cB_id, batch_id=batch_id, owned_credits=200.0, average_purchase_price=12.0)

    # Seed Listing from Company A
    listing = MarketplaceListing(
        id=uuid.uuid4(), ownership_id=own_A.id, seller_company_id=cA_id,
        credits_for_sale=100.0, price_per_credit=15.0, status=ListingStatus.PUBLISHED
    )
    
    # 1. Purchase Order and Transaction: A sells to B
    order_1 = PurchaseOrder(
        id=uuid.uuid4(), listing_id=listing.id, buyer_company_id=cB_id,
        requested_credits=50.0, price_per_credit=15.0, total_price=750.0,
        status=PurchaseOrderStatus.COMPLETED
    )
    tx_1 = Transaction(
        id=uuid.uuid4(), order_id=order_1.id, buyer_company_id=cB_id, seller_company_id=cA_id,
        ownership_id=own_B.id, credits_transferred=50.0, price_per_credit=15.0, total_price=750.0,
        status="COMPLETED", completed_at=datetime.now(timezone.utc)
    )

    # 2. Purchase Order and Transaction: B sells to C
    order_2 = PurchaseOrder(
        id=uuid.uuid4(), listing_id=listing.id, buyer_company_id=cC_id,
        requested_credits=10.0, price_per_credit=20.0, total_price=200.0,
        status=PurchaseOrderStatus.COMPLETED
    )
    tx_2 = Transaction(
        id=uuid.uuid4(), order_id=order_2.id, buyer_company_id=cC_id, seller_company_id=cB_id,
        ownership_id=own_B.id, credits_transferred=10.0, price_per_credit=20.0, total_price=200.0,
        status="COMPLETED", completed_at=datetime.now(timezone.utc)
    )

    db_session.add(co_A)
    db_session.add(co_B)
    db_session.add(co_C)
    db_session.add(user_A)
    db_session.add(user_B)
    db_session.add(reg)
    db_session.add(p)
    db_session.add(batch)
    db_session.add(own_A)
    db_session.add(own_B)
    db_session.add(listing)
    db_session.add(order_1)
    db_session.add(tx_1)
    db_session.add(order_2)
    db_session.add(tx_2)
    db_session.commit()

    # Test Visibility Scopes
    # 1. Company A's trader should only see Transaction 1 (where A is seller). Transaction 2 is invisible.
    headers_A = auth_headers(sub=str(user_A.id), role="TRADER", company_id=str(cA_id))
    resp_A = client.get("/api/v1/transactions", headers=headers_A)
    assert resp_A.status_code == 200
    assert len(resp_A.json()["data"]) == 1
    assert resp_A.json()["data"][0]["buyer"]["id"] == str(cB_id)

    # 2. Company B's trader should see both Transaction 1 (buyer) and Transaction 2 (seller)
    headers_B = auth_headers(sub=str(user_B.id), role="TRADER", company_id=str(cB_id))
    resp_B = client.get("/api/v1/transactions", headers=headers_B)
    assert resp_B.status_code == 200
    assert len(resp_B.json()["data"]) == 2

    # 3. Auditor can view all and search by keyword
    auditor_id = uuid.uuid4()
    auditor = User(id=auditor_id, first_name="Auditor", last_name="Joe", email="auditor@carbonledger.com", hashed_password="h", role=UserRole.AUDITOR, is_active=True)
    db_session.add(auditor)
    db_session.commit()
    
    headers_auditor = auth_headers(sub=str(auditor_id), role="AUDITOR")
    resp_aud = client.get("/api/v1/transactions", headers=headers_auditor)
    assert resp_aud.status_code == 200
    assert len(resp_aud.json()["data"]) == 2

    # Search with company keyword
    resp_search = client.get("/api/v1/transactions?search=Alpha", headers=headers_auditor)
    assert resp_search.status_code == 200
    assert len(resp_search.json()["data"]) == 1
    assert resp_search.json()["data"][0]["buyer"]["id"] == str(cB_id)
