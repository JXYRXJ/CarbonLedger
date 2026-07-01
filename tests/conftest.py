from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Force testing environment before importing settings
import os
os.environ["ENVIRONMENT"] = "testing"
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "testsecretkeytestsecretkeytestsecretkeytestsecretkey"
os.environ["BLOCKCHAIN_ENABLED"] = "False"

from app.core.config import settings
from app.core.database import Base, get_db, engine, SessionLocal as TestingSessionLocal
from app.core.security import create_access_token
from app.main import app


@pytest.fixture(autouse=True)
def setup_test_db() -> Generator:
    """
    Creates the database tables for the duration of the test.
    """
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session() -> Generator:
    """
    Provides a clean, transaction-isolated database session for each test.
    Automatically rolls back changes at completion.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session) -> Generator:
    """
    FastAPI TestClient fixture that overrides get_db dependency.
    """
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers() -> callable:
    """
    Factory utility fixture to generate authorization headers for any test subject.
    """
    def _generate_headers(
        sub: str = "00000000-0000-0000-0000-000000000001",
        role: str = "VIEWER",
        company_id: str = "00000000-0000-0000-0000-000000000002"
    ) -> dict:
        from jose import jwt
        from datetime import datetime, timedelta, timezone
        import uuid
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        payload = {
            "sub": sub,
            "role": role,
            "company_id": company_id,
            "type": "access",
            "jti": str(uuid.uuid4()),
            "exp": int(expire.timestamp())
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return {"Authorization": f"Bearer {token}"}
    return _generate_headers

