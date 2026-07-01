import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.models import Registry, CarbonProject, User, UserRole


def test_permissions_read_only_endpoints(client: TestClient, db_session: Session, auth_headers: callable):
    """
    Tests that non-admin roles (COMPANY_ADMIN, TRADER, AUDITOR, VIEWER)
    have access to read-only endpoints and are NOT blocked with a 403.
    """
    # Seed a registry and project
    reg_id = uuid.uuid4()
    proj_id = uuid.uuid4()
    
    from datetime import date
    reg = Registry(id=reg_id, name="Permissions Registry", country="France", website="https://verra.org", accreditation="ANSI")
    p = CarbonProject(
        id=proj_id,
        registry_id=reg_id,
        project_code="VCS-PERM-01",
        name="Perms Project Test",
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

    # Define roles to test
    read_only_roles = ["COMPANY_ADMIN", "TRADER", "AUDITOR", "VIEWER"]

    for role in read_only_roles:
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            first_name="Test",
            last_name="User",
            email=f"user-{role.lower()}@carbonledger.com",
            hashed_password="password_hash",
            role=getattr(UserRole, role),
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        headers = auth_headers(sub=str(user_id), role=role, company_id=str(uuid.uuid4()))

        # 1. GET /registries
        reg_resp = client.get("/api/v1/registries", headers=headers)
        assert reg_resp.status_code == 200

        # 2. GET /projects
        proj_resp = client.get("/api/v1/projects", headers=headers)
        assert proj_resp.status_code == 200

        # 3. GET /projects/{id}
        details_resp = client.get(f"/api/v1/projects/{proj_id}", headers=headers)
        assert details_resp.status_code == 200


def test_permissions_mutation_endpoints_blocked_for_non_admins(client: TestClient, db_session: Session, auth_headers: callable):
    """
    Tests that non-admin roles are blocked with a 403 Forbidden
    when attempting to mutate registries, projects, or documents.
    """
    non_admin_roles = ["COMPANY_ADMIN", "TRADER", "AUDITOR", "VIEWER"]

    for role in non_admin_roles:
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            first_name="Test",
            last_name="User",
            email=f"mutator-{role.lower()}@carbonledger.com",
            hashed_password="password_hash",
            role=getattr(UserRole, role),
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        headers = auth_headers(sub=str(user_id), role=role, company_id=str(uuid.uuid4()))

        # 1. POST /registries -> 403 Forbidden
        reg_payload = {
            "name": f"Blocked Registry {role}",
            "country": "Germany",
            "website": "https://blocked.de",
            "accreditation": "ISO"
        }
        reg_resp = client.post("/api/v1/registries", json=reg_payload, headers=headers)
        assert reg_resp.status_code == 403

        # 2. POST /projects -> 403 Forbidden
        proj_payload = {
            "registry_id": str(uuid.uuid4()),
            "project_code": f"BL-CODE-{role}",
            "name": "Blocked Project",
            "country": "Germany",
            "project_type": "Wind",
            "verification_standard": "Gold Standard",
            "methodology": "ACM0002",
            "developer": "Blocked Dev",
            "start_date": "2024-01-01",
            "end_date": "2034-12-31"
        }
        proj_resp = client.post("/api/v1/projects", json=proj_payload, headers=headers)
        assert proj_resp.status_code == 403

        # 3. PATCH /projects/{id} -> 403 Forbidden
        patch_resp = client.patch(f"/api/v1/projects/{uuid.uuid4()}", json={"name": "New Name"}, headers=headers)
        assert patch_resp.status_code == 403

        # 4. DELETE /projects/{id} -> 403 Forbidden
        del_resp = client.delete(f"/api/v1/projects/{uuid.uuid4()}", headers=headers)
        assert del_resp.status_code == 403
