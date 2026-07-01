import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.models import User, Company, RefreshToken, UserRole


def test_auth_registration_flow(client: TestClient):
    """
    Tests that registering a new user creates both the company
    and user profiles, returning valid JWT tokens.
    """
    payload = {
        "first_name": "Alice",
        "last_name": "Smith",
        "email": "alice@ecocorp.com",
        "password": "StrongPassword123!",
        "company_name": "EcoCorp Global Ltd",
        "registration_number": "REG-EC-990011",
        "country": "United Kingdom",
        "industry": "Renewables",
        "website": "https://ecocorp.co.uk",
        "wallet_address": "0x3FC91A3afd90b626b217a0BCE2A41f3C8A05a610"
    }
    
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    
    body = response.json()
    assert body["success"] is True
    
    data = body["data"]
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "alice@ecocorp.com"
    assert data["user"]["role"] == "COMPANY_ADMIN"
    assert data["company"]["name"] == "EcoCorp Global Ltd"


def test_auth_login_and_logout_flow(client: TestClient, db_session: Session):
    """
    Tests that a registered user can login with their password,
    receive valid tokens, query their profile, and log out.
    """
    # 1. Register a user first
    reg_payload = {
        "first_name": "Bob",
        "last_name": "Jones",
        "email": "bob@carbontrade.com",
        "password": "StrongPassword123!",
        "company_name": "CarbonTrade Inc",
        "registration_number": "REG-CT-223344",
        "country": "United States",
        "wallet_address": "0x71C7656EC7ab88b098defB751B7401B5f6d8976F"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    # 2. Login
    login_payload = {
        "email": "bob@carbontrade.com",
        "password": "StrongPassword123!"
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    login_data = response.json()["data"]
    access_token = login_data["access_token"]
    refresh_token = login_data["refresh_token"]

    # 3. Query /me profile
    headers = {"Authorization": f"Bearer {access_token}"}
    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["data"]["user"]["email"] == "bob@carbontrade.com"

    # 4. Logout
    logout_payload = {"refresh_token": refresh_token}
    logout_resp = client.post("/api/v1/auth/logout", json=logout_payload, headers=headers)
    assert logout_resp.status_code == 200

    # 5. Check database token was blacklisted
    # Verify is_revoked is True
    from jose import jwt
    from app.core.config import settings
    payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    jti = payload.get("jti")
    
    db_token = db_session.query(RefreshToken).filter(RefreshToken.token_jti == jti).first()
    assert db_token.is_revoked is True


def test_refresh_token_rotation_and_breach_detection(client: TestClient, db_session: Session):
    """
    Tests RTR (Refresh Token Rotation) and breach detection:
    - Refreshing once returns a new token pair and revokes the old token.
    - Presenting the old (already revoked) token triggers token family invalidation.
    """
    # 1. Register and log in
    reg_payload = {
        "first_name": "Charlie",
        "last_name": "Brown",
        "email": "charlie@peanuts.com",
        "password": "StrongPassword123!",
        "company_name": "Peanuts LLC",
        "registration_number": "REG-PE-778899",
        "country": "Germany"
    }
    client.post("/api/v1/auth/register", json=reg_payload)
    
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "charlie@peanuts.com",
        "password": "StrongPassword123!"
    })
    tokens = login_resp.json()["data"]
    refresh_token_1 = tokens["refresh_token"]

    # 2. Refresh the session (First rotation)
    refresh_resp_1 = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token_1})
    assert refresh_resp_1.status_code == 200
    new_tokens = refresh_resp_1.json()["data"]
    access_token_2 = new_tokens["access_token"]
    refresh_token_2 = new_tokens["refresh_token"]

    # Verify token 1 is now marked as revoked in the database
    from jose import jwt
    from app.core.config import settings
    jti_1 = jwt.decode(refresh_token_1, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])["jti"]
    db_token_1 = db_session.query(RefreshToken).filter(RefreshToken.token_jti == jti_1).first()
    assert db_token_1.is_revoked is True

    # 3. Simulate breach: reuse the already revoked refresh_token_1
    breach_resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token_1})
    assert breach_resp.status_code == 403
    assert "compromise detected" in breach_resp.json()["message"].lower()

    # Verify that the active refresh_token_2 was automatically invalidated/revoked
    jti_2 = jwt.decode(refresh_token_2, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])["jti"]
    db_token_2 = db_session.query(RefreshToken).filter(RefreshToken.token_jti == jti_2).first()
    assert db_token_2.is_revoked is True
