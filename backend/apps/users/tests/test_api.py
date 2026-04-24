"""Tests for users API endpoints."""
import pytest
from ninja.testing import TestClient
from django.http import HttpRequest
from apps.users.api import router
from apps.users.models import User
from apps.users.services import UserService


# 创建测试客户端
client = TestClient(router)


@pytest.fixture
def create_user():
    """Fixture to create a test user."""
    def _create_user(username="testuser", email="test@example.com", password="testpass123"):
        return UserService.register(username, email, password)
    return _create_user


@pytest.mark.django_db
class TestRegisterAPI:
    """Test cases for registration endpoint."""

    def test_register_success(self):
        """Test successful user registration via API."""
        response = client.post("/auth/register", json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "password123"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["username"] == "newuser"
        assert data["data"]["email"] == "new@example.com"
        assert "id" in data["data"]

    def test_register_duplicate_username(self, create_user):
        """Test registration fails with duplicate username."""
        create_user(username="existinguser")

        response = client.post("/auth/register", json={
            "username": "existinguser",
            "email": "new@example.com",
            "password": "password123"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 400
        assert "用户名已存在" in data["msg"]

    def test_register_duplicate_email(self, create_user):
        """Test registration fails with duplicate email."""
        create_user(email="existing@example.com")

        response = client.post("/auth/register", json={
            "username": "newuser",
            "email": "existing@example.com",
            "password": "password123"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 400
        assert "邮箱已被注册" in data["msg"]


@pytest.mark.django_db
class TestLoginAPI:
    """Test cases for login endpoint."""

    def test_login_success(self, create_user):
        """Test successful login returns tokens."""
        create_user(username="logintest", password="testpass123")

        response = client.post("/auth/login", json={
            "username": "logintest",
            "password": "testpass123"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["expires_in"] == 7200

    def test_login_wrong_password(self, create_user):
        """Test login fails with wrong password."""
        create_user(username="logintest", password="testpass123")

        response = client.post("/auth/login", json={
            "username": "logintest",
            "password": "wrongpassword"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 401
        assert "用户名或密码错误" in data["msg"]

    def test_login_nonexistent_user(self):
        """Test login fails for non-existent user."""
        response = client.post("/auth/login", json={
            "username": "nonexistent",
            "password": "password123"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 401
        assert "用户名或密码错误" in data["msg"]

    def test_login_disabled_user(self, create_user):
        """Test login fails for disabled user."""
        user = create_user(username="disableduser")
        user.status = User.STATUS_DISABLED
        user.save()

        response = client.post("/auth/login", json={
            "username": "disableduser",
            "password": "testpass123"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 401
        assert "账号已被禁用" in data["msg"]


@pytest.mark.django_db
class TestGetCurrentUserAPI:
    """Test cases for get current user endpoint."""

    def test_get_current_user_success(self, create_user):
        """Test getting current user with valid token."""
        create_user(username="currentuser")
        tokens = UserService.authenticate("currentuser", "testpass123")

        response = client.get("/users/me", headers={
            "Authorization": f"Bearer {tokens['access_token']}"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["username"] == "currentuser"

    def test_get_current_user_no_token(self):
        """Test getting current user without token."""
        response = client.get("/users/me")

        assert response.status_code == 401

    def test_get_current_user_invalid_token(self):
        """Test getting current user with invalid token."""
        response = client.get("/users/me", headers={
            "Authorization": "Bearer invalid_token"
        })

        assert response.status_code == 401


@pytest.mark.django_db
class TestRefreshTokenAPI:
    """Test cases for refresh token endpoint."""

    def test_refresh_token_success(self, create_user):
        """Test successful token refresh."""
        create_user(username="refreshtest")
        tokens = UserService.authenticate("refreshtest", "testpass123")

        response = client.post("/auth/refresh", json={
            "refresh": tokens["refresh_token"]
        })

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["expires_in"] == 7200

    def test_refresh_token_with_access_token(self, create_user):
        """Test refresh fails when using access token."""
        create_user(username="refreshtest")
        tokens = UserService.authenticate("refreshtest", "testpass123")

        response = client.post("/auth/refresh", json={
            "refresh": tokens["access_token"]
        })

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 401
        assert "无效的刷新令牌" in data["msg"]

    def test_refresh_token_invalid(self):
        """Test refresh fails with invalid token."""
        response = client.post("/auth/refresh", json={
            "refresh": "invalid_token"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 401

    def test_refresh_token_expired(self):
        """Test refresh fails with expired token."""
        from core.auth import generate_refresh_token
        from datetime import datetime, timedelta, timezone
        import jwt
        from django.conf import settings

        # 生成一个已过期的token
        expire = datetime.now(timezone.utc) - timedelta(days=1)
        payload = {
            'user_id': 1,
            'exp': expire,
            'type': 'refresh'
        }
        expired_token = jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256')

        response = client.post("/auth/refresh", json={
            "refresh": expired_token
        })

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 401
        assert "令牌已过期" in data["msg"]
