import pytest
from sqlalchemy.orm import Session
from app.services.services import UserService, CompanyService, AuditService
from app.repositories.repositories import UserRepository, CompanyRepository, AuditRepository
from app.models.models import User, Company, AuditLog, UserRole
from app.core.exceptions import BusinessRuleException, DuplicateResourceException


def test_user_service_password_rules(db_session: Session):
    """
    Tests that UserService correctly rejects weak passwords.
    """
    user_repo = UserRepository(db_session)
    user_service = UserService(user_repo)

    weak_user_data = {
        "first_name": "Weak",
        "last_name": "User",
        "email": "weak@test.com",
        "password": "123",  # Too short, missing uppercase/lowercase/special
        "role": UserRole.VIEWER
    }

    with pytest.raises(BusinessRuleException) as excinfo:
        user_service.create_user(weak_user_data)
    
    assert "weak password" in str(excinfo.value).lower()
    # Verify exact validation errors are in exceptions payload
    assert len(excinfo.value.errors) > 0


def test_company_service_duplicate_registries(db_session: Session):
    """
    Tests that CompanyService prevents duplicate registrations of company name/reg numbers.
    """
    comp_repo = CompanyRepository(db_session)
    comp_service = CompanyService(comp_repo)

    company_data = {
        "name": "Unique Company",
        "registration_number": "REG-100200",
        "country": "France"
    }
    
    comp_service.create_company(company_data)

    # Attempting to register the same company name should throw DuplicateResourceException
    with pytest.raises(DuplicateResourceException):
        comp_service.create_company({
            "name": "Unique Company",
            "registration_number": "REG-different",
            "country": "France"
        })

    # Attempting to register the same registration number should throw DuplicateResourceException
    with pytest.raises(DuplicateResourceException):
        comp_service.create_company({
            "name": "Different Company Name",
            "registration_number": "REG-100200",
            "country": "France"
        })


def test_audit_service_event_tracking(db_session: Session):
    """
    Tests that AuditService correctly records system actions in the audit log.
    """
    audit_repo = AuditRepository(db_session)
    audit_service = AuditService(audit_repo)

    # Record login
    import uuid
    user_id = uuid.uuid4()
    company_id = uuid.uuid4()
    
    audit_service.record_login(user_id, company_id, "127.0.0.1", "Mozilla/5.0")
    
    # Assert audit log entry was created
    log = db_session.query(AuditLog).filter(AuditLog.user_id == user_id).first()
    assert log is not None
    assert log.action == "LOGIN"
    assert log.company_id == company_id
    assert log.ip_address == "127.0.0.1"
    assert log.user_agent == "Mozilla/5.0"
