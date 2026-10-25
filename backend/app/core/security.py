"""Authentication and Cryptographic Security Utilities.

Provides secure password hashing via bcrypt and RFC 7519 JWT token issuance/verification.
Zero secret leakage.
"""

from datetime import datetime, timedelta, timezone
import re
from typing import Any
import bcrypt
import jwt

from app.core.config import settings

JWT_ALGORITHM = "HS256"


def get_password_hash(password: str) -> str:
    """Hash a plaintext password using bcrypt with random salt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def validate_password_strength(password: str) -> tuple[bool, str | None]:
    """Validate password complexity.

    Requirements:
    - At least 8 characters
    - At least one letter
    - At least one digit
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Za-z]", password):
        return False, "Password must contain at least one letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."
    return True, None


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token with expiration."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "iat": now,
        "exp": expire,
    })
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode and verify a signed JWT access token.

    Returns payload dict if valid, or None if expired/tampered.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )
        return payload
    except jwt.PyJWTError:
        return None
