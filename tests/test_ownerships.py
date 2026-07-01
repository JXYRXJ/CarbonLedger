import pytest
import uuid
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.models import Registry, CarbonProject, CreditBatch, Ownership, User, UserRole, Company


def test_ownership_total_credits_cap(client: TestClient, db_session: Session, auth_headers: callable):
    """
    Tests that total credits owned across all holdings for a batch cannot exceed
    the batch's total issued credits limit.
    """
    # Seed company, registry, project, batch
    company_id = uuid.uuid4()
    company = Company(id=company_id, name="Test Company", registration_number="12345", country="US")
    reg_id = uuid.uuid4()
    reg = Registry(id=reg_id, name="Own Reg", country="US", website="https://verra.org", accreditation="ANSI")
    proj_id = uuid.uuid4()
    p = CarbonProject(
        id=proj_id, registry_id=reg_id, project_code="VCS-O-01", name="Proj", country="US",
        project_type="Forestry", verification_standard="VCS", methodology="VM0007", developer="Dev",
        start_date=date(2020, 1, 1), end_date=date(2030, 12, 31)
    )
    batch_id = uuid.uuid4()
    batch = CreditBatch(
        id=batch_id, project_id=proj_id, batch_number="BATCH-OWN-01", vintage_year=2024,
        total_credits=1000.0, remaining_credits=1000.0, issuance_date=date(2024, 6, 1)
    )
    db_session.add(company)
    db_session.add(reg)
    db_session.add(p)
    db_session.add(batch)
    db_session.commit()

    # Create initial ownership of 600 credits (Valid)
    from app.services.services import OwnershipService
    from app.repositories.repositories import OwnershipRepository
    own_service = OwnershipService(OwnershipRepository(db_session))
    
    own_service.create_ownership({
        "batch_id": batch_id,
        "company_id": company_id,
        "owned_credits": 600.0,
        "average_purchase_price": 10.0
    })

    # Attempting to assign another 500 credits to another company (Total 1100 > 1000 batch limit) -> should fail
    company_id_2 = uuid.uuid4()
    company_2 = Company(id=company_id_2, name="Test Company 2", registration_number="67890", country="US")
    db_session.add(company_2)
    db_session.commit()

    with pytest.raises(Exception) as excinfo:
        own_service.create_ownership({
            "batch_id": batch_id,
            "company_id": company_id_2,
            "owned_credits": 500.0,
            "average_purchase_price": 12.0
        })
    assert "cannot exceed the batch's total credits limit" in str(excinfo.value).lower()


def test_atomic_ownership_transfer_and_weighted_price(client: TestClient, db_session: Session):
    """
    Tests atomic transferring of credits between two companies. Verifies balance assertions,
    weighted average purchase price calculations, and transaction-safety rollback on failure.
    """
    # Seed two companies
    c1_id = uuid.uuid4()
    c2_id = uuid.uuid4()
    company_1 = Company(id=c1_id, name="Company One", registration_number="C1", country="US")
    company_2 = Company(id=c2_id, name="Company Two", registration_number="C2", country="US")

    reg_id = uuid.uuid4()
    reg = Registry(id=reg_id, name="Reg", country="US", website="https://verra.org", accreditation="ANSI")
    proj_id = uuid.uuid4()
    p = CarbonProject(
        id=proj_id, registry_id=reg_id, project_code="VCS-TR-01", name="Proj", country="US",
        project_type="Forestry", verification_standard="VCS", methodology="VM0007", developer="Dev",
        start_date=date(2020, 1, 1), end_date=date(2030, 12, 31)
    )
    batch_id = uuid.uuid4()
    batch = CreditBatch(
        id=batch_id, project_id=proj_id, batch_number="BATCH-TR-01", vintage_year=2024,
        total_credits=2000.0, remaining_credits=2000.0, issuance_date=date(2024, 6, 1)
    )
    
    # Pre-own credits
    own1 = Ownership(id=uuid.uuid4(), company_id=c1_id, batch_id=batch_id, owned_credits=1000.0, average_purchase_price=10.0)
    own2 = Ownership(id=uuid.uuid4(), company_id=c2_id, batch_id=batch_id, owned_credits=500.0, average_purchase_price=20.0)

    db_session.add(company_1)
    db_session.add(company_2)
    db_session.add(reg)
    db_session.add(p)
    db_session.add(batch)
    db_session.add(own1)
    db_session.add(own2)
    db_session.commit()

    from app.services.services import OwnershipService
    from app.repositories.repositories import OwnershipRepository
    own_service = OwnershipService(OwnershipRepository(db_session))

    # 1. Success transfer of 200 credits at $15/credit
    s, r = own_service.transfer_ownership(
        from_company_id=c1_id,
        to_company_id=c2_id,
        batch_id=batch_id,
        credits=200.0,
        price_per_credit=15.0,
        session=db_session
    )
    db_session.flush()

    assert s.owned_credits == 800.0
    assert r.owned_credits == 700.0
    assert abs(float(r.average_purchase_price) - 18.5714) < 0.01

    # 2. Insufficient credits abort and rollback
    nested = db_session.begin_nested() # Create savepoint
    try:
        own_service.transfer_ownership(
            from_company_id=c1_id,
            to_company_id=c2_id,
            batch_id=batch_id,
            credits=900.0,
            price_per_credit=15.0,
            session=db_session
        )
        db_session.flush()
        nested.commit()
    except Exception as e:
        nested.rollback() # Rollback to savepoint

    # Verify state remains rolled back
    sender_refreshed = db_session.query(Ownership).filter(Ownership.company_id == c1_id).first()
    recipient_refreshed = db_session.query(Ownership).filter(Ownership.company_id == c2_id).first()
    assert sender_refreshed.owned_credits == 800.0
    assert recipient_refreshed.owned_credits == 700.0
