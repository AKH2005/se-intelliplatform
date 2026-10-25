"""Unit Tests for Authentication and Security Module."""

from datetime import timedelta
import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    validate_password_strength,
    verify_password,
)
from app.schemas.auth import UserLoginRequest, UserRegisterRequest


def test_password_hashing_and_verification():
    """Verify that bcrypt properly hashes and verifies passwords."""
    raw = "StrongPass123"
    hashed = get_password_hash(raw)
    assert hashed != raw
    assert hashed.startswith("$2b$")
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword99", hashed) is False


def test_password_strength_validation():
    """Verify password complexity constraints."""
    # Too short
    ok, err = validate_password_strength("Pass1")
    assert ok is False
    assert "at least 8 characters" in err

    # No numbers
    ok, err = validate_password_strength("PasswordOnly")
    assert ok is False
    assert "at least one number" in err

    # No letters
    ok, err = validate_password_strength("1234567890")
    assert ok is False
    assert "at least one letter" in err

    # Valid
    ok, err = validate_password_strength("ValidPassword123")
    assert ok is True
    assert err is None


def test_jwt_token_creation_and_decoding():
    """Verify that JWT tokens can be issued and properly verified."""
    payload = {"sub": "user-uuid-1234", "email": "test@example.com", "role": "developer"}
    token = create_access_token(payload, expires_delta=timedelta(minutes=15))
    assert isinstance(token, str)
    assert len(token) > 20

    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "user-uuid-1234"
    assert decoded["email"] == "test@example.com"
    assert decoded["role"] == "developer"
    assert "exp" in decoded


def test_jwt_token_expired_fails():
    """Verify that expired tokens return None when decoded."""
    payload = {"sub": "user-uuid-1234"}
    # Token expired 10 minutes ago
    token = create_access_token(payload, expires_delta=timedelta(minutes=-10))
    decoded = decode_access_token(token)
    assert decoded is None


def test_jwt_tampered_token_fails():
    """Verify that an altered token fails verification."""
    token = create_access_token({"sub": "user-uuid"})
    tampered = token[:-4] + "abcd"
    decoded = decode_access_token(tampered)
    assert decoded is None


def test_register_schema_validation():
    """Verify Pydantic validation on registration schema."""
    # Passwords mismatch
    with pytest.raises(ValueError, match="Passwords do not match"):
        UserRegisterRequest(
            name="Alice",
            email="alice@example.com",
            password="Password123",
            confirm_password="DifferentPassword456",
        )

    # Weak password (length >= 8, but no numbers)
    with pytest.raises(ValueError, match="Password must contain at least one number"):
        UserRegisterRequest(
            name="Alice",
            email="alice@example.com",
            password="NoNumbersHere",
            confirm_password="NoNumbersHere",
        )

    # Valid registration data
    req = UserRegisterRequest(
        name="Alice User",
        email="Alice@Example.COM",
        password="ValidPassword123",
        confirm_password="ValidPassword123",
    )
    assert req.name == "Alice User"
    assert req.email == "alice@example.com"
