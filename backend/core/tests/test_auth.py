"""Tests for core auth module."""
import pytest
import jwt
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
from django.conf import settings
from core.auth import (
    generate_access_token,
    generate_refresh_token,
    decode_token,
    JWTAuth
)
from core.exceptions import AuthorizationError
from apps.users.models import User
from apps.users.services import UserService


class TestGenerateAccessToken:
    """Test cases for generate_access_token function."""

    def test_generate_access_token_returns_valid_jwt(self):
        """Test access token is valid JWT with correct payload."""
        user_id = 123
        token = generate_access_token(user_id)

        # 解码验证
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=['HS256'])

        assert payload['user_id'] == user_id
        assert payload['type'] == 'access'
        assert 'exp' in payload

    def test_access_token_expiry(self):
        """Test access token expires after configured minutes."""
        user_id = 123
        token = generate_access_token(user_id)

        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=['HS256'])
        exp_timestamp = payload['exp']
        exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)

        expected_expiry = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES)
        # 允许1秒误差
        assert abs((exp_datetime - expected_expiry).total_seconds()) < 2


class TestGenerateRefreshToken:
    """Test cases for generate_refresh_token function."""

    def test_generate_refresh_token_returns_valid_jwt(self):
        """Test refresh token is valid JWT with correct payload."""
        user_id = 456
        token = generate_refresh_token(user_id)

        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=['HS256'])

        assert payload['user_id'] == user_id
        assert payload['type'] == 'refresh'
        assert 'exp' in payload

    def test_refresh_token_expiry(self):
        """Test refresh token expires after configured days."""
        user_id = 456
        token = generate_refresh_token(user_id)

        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=['HS256'])
        exp_timestamp = payload['exp']
        exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)

        expected_expiry = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)
        # 允许1秒误差
        assert abs((exp_datetime - expected_expiry).total_seconds()) < 2


class TestDecodeToken:
    """Test cases for decode_token function."""

    def test_decode_valid_token(self):
        """Test decoding valid token returns payload."""
        user_id = 789
        token = generate_access_token(user_id)

        payload = decode_token(token)

        assert payload['user_id'] == user_id
        assert payload['type'] == 'access'

    def test_decode_expired_token_raises_error(self):
        """Test decoding expired token raises AuthorizationError."""
        # 生成一个已过期的token
        expire = datetime.now(timezone.utc) - timedelta(hours=1)
        payload = {
            'user_id': 1,
            'exp': expire,
            'type': 'access'
        }
        expired_token = jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256')

        with pytest.raises(AuthorizationError, match="令牌已过期"):
            decode_token(expired_token)

    def test_decode_invalid_token_raises_error(self):
        """Test decoding invalid token raises AuthorizationError."""
        with pytest.raises(AuthorizationError, match="无效的令牌"):
            decode_token("invalid_token")

    def test_decode_token_with_wrong_secret(self):
        """Test decoding token with wrong secret raises error."""
        token = jwt.encode({'user_id': 1}, "wrong_secret", algorithm='HS256')

        with pytest.raises(AuthorizationError, match="无效的令牌"):
            decode_token(token)


@pytest.mark.django_db
class TestJWTAuth:
    """Test cases for JWTAuth class."""

    def test_authenticate_with_valid_access_token(self):
        """Test authentication with valid access token returns user."""
        # 创建测试用户
        user = UserService.register(
            username="authtest",
            email="auth@example.com",
            password="testpass123"
        )
        token = generate_access_token(user.id)

        auth = JWTAuth()
        mock_request = MagicMock()

        result = auth.authenticate(mock_request, token)

        assert result is not None
        assert result.id == user.id
        assert result.username == "authtest"

    def test_authenticate_with_empty_token(self):
        """Test authentication with empty token returns None."""
        auth = JWTAuth()
        mock_request = MagicMock()

        result = auth.authenticate(mock_request, "")

        assert result is None

    def test_authenticate_with_refresh_token(self):
        """Test authentication with refresh token returns None."""
        user = UserService.register(
            username="authtest2",
            email="auth2@example.com",
            password="testpass123"
        )
        # 使用 refresh token 而不是 access token
        token = generate_refresh_token(user.id)

        auth = JWTAuth()
        mock_request = MagicMock()

        result = auth.authenticate(mock_request, token)

        assert result is None

    def test_authenticate_with_expired_token(self):
        """Test authentication with expired token raises AuthorizationError."""
        expire = datetime.now(timezone.utc) - timedelta(hours=1)
        payload = {
            'user_id': 1,
            'exp': expire,
            'type': 'access'
        }
        expired_token = jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256')

        auth = JWTAuth()
        mock_request = MagicMock()

        with pytest.raises(AuthorizationError, match="令牌已过期"):
            auth.authenticate(mock_request, expired_token)

    def test_authenticate_with_nonexistent_user(self):
        """Test authentication with non-existent user returns None."""
        # 生成一个有效但用户不存在的token
        token = generate_access_token(99999)

        auth = JWTAuth()
        mock_request = MagicMock()

        result = auth.authenticate(mock_request, token)

        assert result is None

    def test_authenticate_with_invalid_token(self):
        """Test authentication with invalid token returns None."""
        auth = JWTAuth()
        mock_request = MagicMock()

        result = auth.authenticate(mock_request, "invalid_token")

        assert result is None

    def test_authenticate_with_token_missing_user_id(self):
        """Test authentication with token missing user_id returns None."""
        # 生成一个没有 user_id 的token
        expire = datetime.now(timezone.utc) + timedelta(hours=1)
        payload = {
            'exp': expire,
            'type': 'access'
        }
        token = jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256')

        auth = JWTAuth()
        mock_request = MagicMock()

        result = auth.authenticate(mock_request, token)

        assert result is None
