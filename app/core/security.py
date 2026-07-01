import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union
import bcrypt
from jose import jwt, JWTError

from app.core.config import settings
from app.core.exceptions import InvalidTokenException, ExpiredTokenException


def get_password_hash(password: str) -> str:
    """
    Hashes a plain-text password using bcrypt.
    """
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_pwd = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_pwd.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain-text password against a hashed bcrypt password.
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def create_access_token(
    subject: Union[str, Any],
    role: str,
    company_id: Optional[Union[str, Any]] = None,
    expires_delta: Optional[timedelta] = None
) -> tuple[str, str]:
    """
    Generates a JWT access token for a subject.
    Returns: A tuple containing (token_string, jti_string)
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    jti = str(uuid.uuid4())
    to_encode = {
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "sub": str(subject),
        "role": role,
        "company_id": str(company_id) if company_id else None,
        "type": "access",
        "jti": jti
    }
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt, jti


def create_refresh_token(
    subject: Union[str, Any],
    role: str,
    company_id: Optional[Union[str, Any]] = None,
    expires_delta: Optional[timedelta] = None
) -> tuple[str, str]:
    """
    Generates a JWT refresh token for a subject.
    Returns: A tuple containing (token_string, jti_string)
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    jti = str(uuid.uuid4())
    to_encode = {
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "sub": str(subject),
        "role": role,
        "company_id": str(company_id) if company_id else None,
        "type": "refresh",
        "jti": jti
    }
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt, jti


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decodes and validates a JWT token using python-jose.
    Raises ExpiredTokenException or InvalidTokenException for verification failures.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError as exc:
        raise ExpiredTokenException("Signature has expired") from exc
    except JWTError as exc:
        raise InvalidTokenException("Invalid token signature or structure") from exc
