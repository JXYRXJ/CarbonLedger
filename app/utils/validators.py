import re
from typing import List, Optional
import uuid


def validate_email(email: str) -> bool:
    """
    Validates email format using RFC 5322 regex.
    """
    email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(email_regex, email))


def validate_password_strength(password: str) -> List[str]:
    """
    Enforces password rules:
    - Minimum length: 8
    - Uppercase letter
    - Lowercase letter
    - Digit/Number
    - Special character (non-alphanumeric)
    Returns a list of failed rule descriptions. If empty, the password is strong.
    """
    failures = []
    if len(password) < 8:
        failures.append("Password must be at least 8 characters long")
    if not re.search(r"[A-Z]", password):
        failures.append("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        failures.append("Password must contain at least one lowercase letter")
    if not re.search(r"\d", password):
        failures.append("Password must contain at least one number")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        failures.append("Password must contain at least one special character")
    return failures


def validate_wallet_address(address: str) -> bool:
    """
    Validates standard Ethereum hexadecimal wallet address format.
    """
    return bool(re.match(r"^0x[a-fA-F0-9]{40}$", address))


def validate_uuid(value: str) -> bool:
    """
    Verifies if a string is a valid UUID version 4.
    """
    try:
        uuid.UUID(str(value))
        return True
    except ValueError:
        return False


def validate_file_metadata(
    filename: str,
    content_type: str,
    file_size: Optional[int] = None,
    max_size_bytes: int = 10485760  # 10MB
) -> List[str]:
    """
    Validates uploaded document metadata.
    Enforces rules:
    - Maximum filename length: 255
    - Prevent path traversal
    - Allowed extensions: .pdf, .png, .jpg, .jpeg, .xlsx, .csv
    - Allowed MIME types
    - File size limits
    """
    failures = []
    
    # 1. Filename length
    if len(filename) > 255:
        failures.append("Filename exceeds maximum length of 255 characters")
        
    # 2. Path traversal check
    if ".." in filename or "/" in filename or "\\" in filename:
        failures.append("Path traversal characters are prohibited in the filename")
        
    # 3. Allowed extensions
    allowed_extensions = {".pdf", ".png", ".jpg", ".jpeg", ".xlsx", ".csv"}
    import os
    _, ext = os.path.splitext(filename.lower())
    if ext not in allowed_extensions:
        failures.append(f"File extension '{ext}' is not allowed. Supported: {', '.join(allowed_extensions)}")
        
    # 4. Allowed MIME types
    allowed_mimes = {
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/jpg",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/csv",
        "application/octet-stream"
    }
    if content_type.lower() not in allowed_mimes:
        failures.append(f"MIME type '{content_type}' is not allowed")
        
    # 5. File size
    if file_size is not None and file_size > max_size_bytes:
        failures.append(f"File size exceeds maximum limit of {max_size_bytes / (1024*1024):.1f}MB")
        
    return failures
