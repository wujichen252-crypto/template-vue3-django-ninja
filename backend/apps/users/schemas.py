"""Ninja schemas for users."""
from ninja import Schema
from typing import Optional
from datetime import datetime


class RegisterIn(Schema):
    """Registration request schema."""
    username: str
    password: str
    email: str


class LoginIn(Schema):
    """Login request schema."""
    username: str
    password: str


class UserOut(Schema):
    """User response schema."""
    id: int
    username: str
    email: str
    avatar_url: Optional[str] = None
    status: int
    created_at: datetime


class TokenOut(Schema):
    """Token response schema."""
    access_token: str
    refresh_token: str
    expires_in: int


class RefreshTokenIn(Schema):
    """Refresh token request schema."""
    refresh: str
