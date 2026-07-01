import pytest
import uuid
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.models import Registry, CarbonProject, ProjectDocument, DocumentType, CreditBatch, User, UserRole


def test_project_creation_and_date_rules(client: TestClient, db_session: Session, auth_headers: callable):
    """
    Tests registering carbon offset projects. Validates that project code is unique
    and start/end dates are sequential.
    """
    admin_id = uuid.uuid4()
    admin_user = User(
        id=admin_id,
        first_name="Admin",
        last_name="User",
        email="admin-proj-create@carbonledger.com",
        hashed_password="hashed_password",
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(admin_user)
    
    # Seed a registry
    registry_id = uuid.uuid4()
    reg = Registry(
        id=registry_id,
        name="Verra Projects Registry",
        country="France",
        website="https://verra.org",
        accreditation="ANSI"
    )
    db_session.add(reg)
    db_session.commit()

    headers = auth_headers(sub=str(admin_id), role="ADMIN")
    
    # 1. Successful project creation
    payload = {
        "registry_id": str(registry_id),
        "project_code": "VCS-980",
        "name": "Green Amazon Forest Preservation",
        "country": "Brazil",
        "project_type": "Forestry",
        "verification_standard": "VCS",
        "methodology": "VM0007",
        "developer": "Greenhouse LLC",
        "start_date": "2024-01-01",
        "end_date": "2034-12-31",
        "description": "Preserving the lungs of the earth"
    }
    resp = client.post("/api/v1/projects", json=payload, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["data"]["project_code"] == "VCS-980"

    # 2. Reject duplicate code
    dup_resp = client.post("/api/v1/projects", json=payload, headers=headers)
    assert dup_resp.status_code == 409

    # 3. Reject end date occurring before start date
    invalid_dates_payload = payload.copy()
    invalid_dates_payload["project_code"] = "VCS-different"
    invalid_dates_payload["start_date"] = "2024-12-31"
    invalid_dates_payload["end_date"] = "2024-01-01"
    
    date_resp = client.post("/api/v1/projects", json=invalid_dates_payload, headers=headers)
    assert date_resp.status_code == 422


def test_project_document_attachments_crud(client: TestClient, db_session: Session, auth_headers: callable):
    """
    Tests documents attachment, update, and deletion on a carbon project.
    """
    admin_id = uuid.uuid4()
    admin_user = User(
        id=admin_id,
        first_name="Admin",
        last_name="User",
        email="admin-doc-create@carbonledger.com",
        hashed_password="hashed_password",
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(admin_user)

    # Seed project
    registry_id = uuid.uuid4()
    project_id = uuid.uuid4()
    
    reg = Registry(id=registry_id, name="Doc Registry", country="France", website="https://verra.org", accreditation="ANSI")
    p = CarbonProject(
        id=project_id,
        registry_id=registry_id,
        project_code="VCS-DOCS-01",
        name="Document Project Test",
        country="France",
        project_type="Solar",
        verification_standard="VCS",
        methodology="ACM0002",
        developer="Developer Ltd",
        start_date=date(2020, 1, 1),
        end_date=date(2030, 12, 31)
    )
    db_session.add(reg)
    db_session.add(p)
    db_session.commit()

    headers = auth_headers(sub=str(admin_id), role="ADMIN")

    # 1. Attach Document
    doc_payload = {
        "document_type": "Verification Certificate",
        "file_name": "verification_report.pdf",
        "file_url": "https://storage.carbonledger.com/docs/verification_report.pdf"
    }
    attach_resp = client.post(f"/api/v1/projects/{project_id}/documents", json=doc_payload, headers=headers)
    assert attach_resp.status_code == 201
    doc_id = attach_resp.json()["data"]["id"]
    assert attach_resp.json()["data"]["file_name"] == "verification_report.pdf"

    # 2. Update Document
    update_payload = {"file_name": "updated_report.pdf"}
    up_resp = client.patch(f"/api/v1/documents/{doc_id}", json=update_payload, headers=headers)
    assert up_resp.status_code == 200
    assert up_resp.json()["data"]["file_name"] == "updated_report.pdf"

    # 3. Delete Document
    del_resp = client.delete(f"/api/v1/documents/{doc_id}", headers=headers)
    assert del_resp.status_code == 200
    
    # Confirm it was physically deleted
    assert db_session.query(ProjectDocument).filter(ProjectDocument.id == uuid.UUID(doc_id)).first() is None
