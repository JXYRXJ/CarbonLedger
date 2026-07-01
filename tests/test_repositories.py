import pytest
from sqlalchemy.orm import Session
from app.repositories.repositories import UserRepository, CompanyRepository
from app.models.models import User, UserRole, Company


def test_repository_crud_ops(db_session: Session):
    """
    Tests generic BaseRepository CRUD operations:
    - Create Company and User
    - Find one and find by ID
    - Update
    - Count and Paginate
    - Soft delete behavior
    """
    comp_repo = CompanyRepository(db_session)
    user_repo = UserRepository(db_session)

    # 1. Create
    company = comp_repo.create({
        "name": "Test Repo Company",
        "registration_number": "REG-REP-11",
        "country": "Germany"
    })
    assert company.id is not None

    user = user_repo.create({
        "first_name": "Test",
        "last_name": "User",
        "email": "repo@test.com",
        "hashed_password": "password_hash",
        "role": UserRole.TRADER,
        "company_id": company.id,
        "is_active": True
    })
    assert user.id is not None

    # 2. Find one and count
    found_user = user_repo.find_one(email="repo@test.com")
    assert found_user is not None
    assert found_user.id == user.id

    cnt = user_repo.count(company_id=company.id)
    assert cnt == 1

    # 3. Update
    updated_user = user_repo.update(user, {"first_name": "UpdatedName"})
    assert updated_user.first_name == "UpdatedName"

    # 4. Paginate
    items, total = user_repo.paginate(page=1, limit=5, company_id=company.id)
    assert total == 1
    assert len(items) == 1
    assert items[0].id == user.id

    # 5. Soft delete
    user_repo.soft_delete(user)
    
    # Querying by find_by_id should return None (soft deleted filter)
    assert user_repo.find_by_id(user.id) is None
    # Counting should return 0
    assert user_repo.count(company_id=company.id) == 0

    # Verify that the record is still physically in the database but flagged
    db_record = db_session.query(User).filter(User.id == user.id).first()
    assert db_record is not None
    assert db_record.deleted_at is not None
