import pytest
import uuid
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.models import Registry, User, UserRole, CarbonProject, CreditBatch


def test_registry_create_validation_and_uniqueness(client: TestClient, db_session: Session, auth_headers: callable):
    """
    Tests registering a new carbon registry. Ensures validators enforce URL patterns
    and block duplicate registry profile creations.
    """
    admin_id = uuid.uuid4()
    admin_user = User(
        id=admin_id,
        first_name="Admin",
        last_name="User",
        email="admin-reg-create@carbonledger.com",
        hashed_password="hashed_password",
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(admin_user)
    db_session.commit()
    
    headers = auth_headers(sub=str(admin_id), role="ADMIN")
    
    # 1. Successful Create
    payload = {
        "name": "Verra Test Registry",
        "country": "United States",
        "website": "https://verra.org",
        "accreditation": "ANSI Standards Board",
        "description": "Verification of climate impacts"
    }
    resp = client.post("/api/v1/registries", json=payload, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["data"]["name"] == "Verra Test Registry"

    # 2. Reject Duplicate Name
    dup_resp = client.post("/api/v1/registries", json=payload, headers=headers)
    assert dup_resp.status_code == 409
    assert "already exists" in dup_resp.json()["message"].lower()

    # 3. Reject Invalid URL Website Format
    invalid_url_payload = payload.copy()
    invalid_url_payload["name"] = "Different Name"
    invalid_url_payload["website"] = "invalid-url-domain"
    url_resp = client.post("/api/v1/registries", json=invalid_url_payload, headers=headers)
    assert url_resp.status_code == 400
    assert "website url" in url_resp.json()["message"].lower()


def test_registry_statistics_aggregation(client: TestClient, db_session: Session, auth_headers: callable):
    """
    Seeds registries, projects, and batches to verify that registry statistics
    properly count active projects, inactive projects, and issued credits.
    """
    viewer_id = uuid.uuid4()
    viewer_user = User(
        id=viewer_id,
        first_name="Viewer",
        last_name="User",
        email="viewer-reg-stats@carbonledger.com",
        hashed_password="hashed_password",
        role=UserRole.VIEWER,
        is_active=True
    )
    
    registry_id = uuid.uuid4()
    project_id_1 = uuid.uuid4()
    project_id_2 = uuid.uuid4()
    
    # Create registry
    reg = Registry(
        id=registry_id,
        name="Stats Registry",
        country="France",
        website="https://statsreg.fr",
        accreditation="ISO 14065"
    )
    
    p1 = CarbonProject(
        id=project_id_1,
        registry_id=registry_id,
        project_code=str(uuid.uuid4())[:8],
        name="Active Forestry Project",
        country="France",
        project_type="Forestry",
        verification_standard="VCS",
        methodology="VM0007",
        developer="GreenDeveloper",
        start_date=date(2020, 1, 1),
        end_date=date(2030, 12, 31),
        status="ACTIVE"
    )
    p2 = CarbonProject(
        id=project_id_2,
        registry_id=registry_id,
        project_code=str(uuid.uuid4())[:8],
        name="Inactive Solar Project",
        country="France",
        project_type="Solar",
        verification_standard="Gold Standard",
        methodology="ACM0002",
        developer="GreenDeveloper",
        start_date=date(2020, 1, 1),
        end_date=date(2030, 12, 31),
        status="PENDING"
    )
    
    # Create batch under project 1 with a valid issuance_date
    batch = CreditBatch(
        id=uuid.uuid4(),
        project_id=project_id_1,
        batch_number="BATCH-ST-001",
        vintage_year=2024,
        total_credits=10000.0,
        remaining_credits=8000.0,
        issuance_date=date(2024, 6, 1),
        status="ACTIVE"
    )
    
    db_session.add(viewer_user)
    db_session.add(reg)
    db_session.add(p1)
    db_session.add(p2)
    db_session.add(batch)
    db_session.commit()

    headers = auth_headers(sub=str(viewer_id), role="VIEWER")

    # Call Statistics endpoint
    stats_resp = client.get(f"/api/v1/registries/{registry_id}/statistics", headers=headers)
    assert stats_resp.status_code == 200
    
    stats = stats_resp.json()["data"]
    assert stats["projects_count"] == 2
    assert stats["active_projects"] == 1
    assert stats["inactive_projects"] == 1
    assert stats["batches_count"] == 1
    assert stats["total_credits_issued"] == 10000.0
