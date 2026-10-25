"""Pydantic v2 Schemas for Authentication Operations."""

import re
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.core.security import validate_password_strength
from app.models.user import UserRole


EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class UserBase(BaseModel):
    """Base fields for User representation."""
    name: str = Field(..., min_length=2, max_length=255, description="User full display name")
    email: str = Field(..., description="Valid user email address")

    @field_validator("name")
    @classmethod
    def validate_name_not_blank(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Name cannot be empty or whitespace only.")
        return s

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        normalized = v.strip().lower()
        if not EMAIL_REGEX.match(normalized):
            raise ValueError("Invalid email address format.")
        return normalized


class UserRegisterRequest(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=8, max_length=128, description="Plaintext password")
    confirm_password: str = Field(..., min_length=8, max_length=128, description="Password confirmation")

    @model_validator(mode="after")
    def validate_passwords_match_and_strength(self) -> "UserRegisterRequest":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        is_strong, reason = validate_password_strength(self.password)
        if not is_strong:
            raise ValueError(reason or "Password does not meet complexity requirements.")
        return self


class UserLoginRequest(BaseModel):
    """Schema for user login credentials."""
    email: str = Field(..., description="User registered email")
    password: str = Field(..., min_length=1, max_length=128, description="User password")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        normalized = v.strip().lower()
        if not EMAIL_REGEX.match(normalized):
            raise ValueError("Invalid email address format.")
        return normalized


class UserResponse(UserBase):
    """Public user profile response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="Unique user UUID")
    role: UserRole = Field(default=UserRole.USER, description="User authorization role")
    is_active: bool = Field(default=True, description="Account active status")
    created_at: datetime = Field(..., description="Registration timestamp")


class TokenResponse(BaseModel):
    """Bearer token response payload."""
    access_token: str = Field(..., description="JWT Bearer token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(..., description="Authenticated user profile")
