"""Tests for users services module."""
import pytest
from unittest.mock import patch, MagicMock
from django.core.cache import cache
from apps.users.models import User
from apps.users.services import UserService
from core.exceptions import AuthenticationError


@pytest.mark.django_db
class TestUserService:
    """Test cases for UserService."""

    def test_hash_password(self):
        """Test password hashing returns valid bcrypt hash."""
        password = "test_password123"
        hashed = UserService.hash_password(password)

        assert hashed.startswith('$2')
        assert UserService.verify_password(password, hashed) is True

    def test_verify_password_with_wrong_password(self):
        """Test verify_password returns False for incorrect password."""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = UserService.hash_password(password)

        assert UserService.verify_password(wrong_password, hashed) is False

    def test_register_success(self):
        """Test successful user registration."""
        user = UserService.register(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.status == User.STATUS_NORMAL

    def test_register_duplicate_username(self):
        """Test registration fails with duplicate username."""
        UserService.register(
            username="testuser",
            email="test1@example.com",
            password="testpass123"
        )

        with pytest.raises(ValueError, match="用户名已存在"):
            UserService.register(
                username="testuser",
                email="test2@example.com",
                password="testpass123"
            )

    def test_register_duplicate_email(self):
        """Test registration fails with duplicate email."""
        UserService.register(
            username="user1",
            email="test@example.com",
            password="testpass123"
        )

        with pytest.raises(ValueError, match="邮箱已被注册"):
            UserService.register(
                username="user2",
                email="test@example.com",
                password="testpass123"
            )

    def test_authenticate_success(self):
        """Test successful authentication returns tokens."""
        UserService.register(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        tokens = UserService.authenticate("testuser", "testpass123")

        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["expires_in"] == 7200
        assert isinstance(tokens["access_token"], str)
        assert isinstance(tokens["refresh_token"], str)

    def test_authenticate_wrong_password(self):
        """Test authentication fails with wrong password."""
        UserService.register(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        with pytest.raises(AuthenticationError, match="用户名或密码错误"):
            UserService.authenticate("testuser", "wrongpassword")

    def test_authenticate_nonexistent_user(self):
        """Test authentication fails for non-existent user."""
        with pytest.raises(AuthenticationError, match="用户名或密码错误"):
            UserService.authenticate("nonexistent", "password123")

    def test_authenticate_disabled_user(self):
        """Test authentication fails for disabled user."""
        user = UserService.register(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        user.status = User.STATUS_DISABLED
        user.save()

        with pytest.raises(AuthenticationError, match="账号已被禁用"):
            UserService.authenticate("testuser", "testpass123")

    def test_authenticate_lockout_after_max_attempts(self):
        """Test account lockout after maximum failed attempts."""
        UserService.register(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        # 5次失败登录
        for _ in range(5):
            with pytest.raises(AuthenticationError):
                UserService.authenticate("testuser", "wrongpassword")

        # 第6次应该被锁定
        with pytest.raises(AuthenticationError, match="登录尝试次数过多"):
            UserService.authenticate("testuser", "testpass123")

    def test_get_user_by_id_from_database(self):
        """Test get_user_by_id retrieves user from database."""
        user = UserService.register(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        retrieved = UserService.get_user_by_id(user.id)

        assert retrieved is not None
        assert retrieved.id == user.id
        assert retrieved.username == user.username

    def test_get_user_by_id_from_cache(self):
        """Test get_user_by_id retrieves user from cache."""
        user = UserService.register(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        # 第一次查询，缓存到 Redis
        UserService.get_user_by_id(user.id)

        # 第二次查询应该从缓存获取
        with patch.object(User.objects, 'get') as mock_get:
            cached_user = UserService.get_user_by_id(user.id)
            mock_get.assert_not_called()
            assert cached_user.id == user.id

    def test_get_user_by_id_not_found(self):
        """Test get_user_by_id returns None for non-existent user."""
        result = UserService.get_user_by_id(99999)
        assert result is None

    def test_get_user_from_token_valid(self):
        """Test get_user_from_token with valid access token."""
        user = UserService.register(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        tokens = UserService.authenticate("testuser", "testpass123")

        retrieved = UserService.get_user_from_token(tokens["access_token"])

        assert retrieved is not None
        assert retrieved.id == user.id

    def test_get_user_from_token_invalid(self):
        """Test get_user_from_token with invalid token."""
        result = UserService.get_user_from_token("invalid_token")
        assert result is None

    def test_refresh_access_token_success(self):
        """Test successful token refresh."""
        UserService.register(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        tokens = UserService.authenticate("testuser", "testpass123")

        new_tokens = UserService.refresh_access_token(tokens["refresh_token"])

        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens
        assert new_tokens["expires_in"] == 7200
        # 新token应该与旧token不同
        assert new_tokens["access_token"] != tokens["access_token"]

    def test_refresh_access_token_with_access_token(self):
        """Test refresh fails when using access token instead of refresh token."""
        UserService.register(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        tokens = UserService.authenticate("testuser", "testpass123")

        with pytest.raises(AuthenticationError, match="无效的刷新令牌"):
            UserService.refresh_access_token(tokens["access_token"])

    def test_refresh_access_token_user_not_found(self):
        """Test refresh fails when user no longer exists."""
        from core.auth import generate_refresh_token

        # 生成一个有效但用户不存在的token
        fake_token = generate_refresh_token(99999)

        with pytest.raises(AuthenticationError, match="用户不存在"):
            UserService.refresh_access_token(fake_token)

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear cache before each test."""
        cache.clear()
        yield
        cache.clear()
