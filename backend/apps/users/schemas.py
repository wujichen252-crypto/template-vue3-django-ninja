"""Ninja schemas for users."""
from ninja import Schema
from typing import Optional
from datetime import datetime
from pydantic import field_validator, EmailStr
import re


class RegisterIn(Schema):
    """Registration request schema."""
    username: str
    password: str
    email: str

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """验证用户名格式和长度"""
        if not re.match(r'^[a-zA-Z0-9_\u4e00-\u9fa5]+$', v):
            raise ValueError('用户名只能包含字母、数字、下划线和中文')
        if len(v) < 3 or len(v) > 32:
            raise ValueError('用户名长度必须在 3-32 个字符之间')
        return v.strip()

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """验证密码强度"""
        if len(v) < 8:
            raise ValueError('密码长度不能少于 8 个字符')
        if len(v) > 128:
            raise ValueError('密码长度不能超过 128 个字符')
        if not re.search(r'[A-Z]', v):
            raise ValueError('密码必须包含至少一个大写字母')
        if not re.search(r'[a-z]', v):
            raise ValueError('密码必须包含至少一个小写字母')
        if not re.search(r'\d', v):
            raise ValueError('密码必须包含至少一个数字')
        return v

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """验证邮箱格式"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('邮箱格式不正确')
        return v.strip().lower()


class LoginIn(Schema):
    """Login request schema."""
    username: str
    password: str

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('用户名不能为空')
        return v.strip()

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v:
            raise ValueError('密码不能为空')
        return v


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

    @field_validator('refresh')
    @classmethod
    def validate_refresh(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('刷新令牌不能为空')
        return v.strip()


class ChangePasswordIn(Schema):
    """Change password request schema."""
    old_password: str
    new_password: str

    @field_validator('old_password')
    @classmethod
    def validate_old_password(cls, v: str) -> str:
        if not v:
            raise ValueError('旧密码不能为空')
        return v

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """验证新密码强度"""
        if len(v) < 8:
            raise ValueError('密码长度不能少于 8 个字符')
        if len(v) > 128:
            raise ValueError('密码长度不能超过 128 个字符')
        if not re.search(r'[A-Z]', v):
            raise ValueError('密码必须包含至少一个大写字母')
        if not re.search(r'[a-z]', v):
            raise ValueError('密码必须包含至少一个小写字母')
        if not re.search(r'\d', v):
            raise ValueError('密码必须包含至少一个数字')
        return v
