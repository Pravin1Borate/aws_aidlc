from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("email", mode="before")
    @classmethod
    def email_lowercase(cls, v: str) -> str:
        return v.lower() if isinstance(v, str) else v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email", mode="before")
    @classmethod
    def email_lowercase(cls, v: str) -> str:
        return v.lower() if isinstance(v, str) else v


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: Optional[str] = None
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class User(BaseModel):
    id: str
    email: str
    password_hash: str
    full_name: Optional[str] = None
    failed_login_attempts: int = 0
    lockout_until: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
