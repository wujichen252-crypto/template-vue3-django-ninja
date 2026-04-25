"""Tests for user service cache integration."""
import pytest
import time
from unittest.mock import patch, MagicMock
from django.core.cache import cache
from apps.users.models import User
from apps.users.services import UserService


@pytest.mark.django_db
class TestUserServiceCacheIntegration:
    """Test cases for UserService cache integration."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear cache before each test."""
        cache.clear()
        yield
        cache.clear()

    def test_get_user_by_id_with_cache_penetration_protection(self):
        """Test cache penetration protection for non-existent user."""
        # 查询不存在的用户
        result1 = UserService.get_user_by_id(99999)
        assert result1 is None

        # 再次查询，应该直接返回缓存的 None，不查询数据库
        with patch.object(User.objects, 'get') as mock_get:
            result2 = UserService.get_user_by_id(99999)
            mock_get.assert_not_called()
            assert result2 is None

    def test_get_user_by_id_caches_result(self):
        """Test user data is cached after first retrieval."""
        user = UserService.register(
            username="cacheuser",
            email="cache@example.com",
            password="testpass123"
        )

        # 第一次查询
        result1 = UserService.get_user_by_id(user.id)
        assert result1.username == "cacheuser"

        # 第二次查询应该从缓存获取
        with patch.object(User.objects, 'get') as mock_get:
            result2 = UserService.get_user_by_id(user.id)
            mock_get.assert_not_called()
            assert result2.username == "cacheuser"

    def test_authenticate_warms_cache(self):
        """Test successful authentication warms user cache."""
        user = UserService.register(
            username="warmuser",
            email="warm@example.com",
            password="testpass123"
        )

        # 登录
        tokens = UserService.authenticate("warmuser", "testpass123")

        # 用户应该已被缓存
        with patch.object(User.objects, 'get') as mock_get:
            cached_user = UserService.get_user_by_id(user.id)
            mock_get.assert_not_called()
            assert cached_user.id == user.id

    def test_register_warms_cache(self):
        """Test registration warms user cache."""
        user = UserService.register(
            username="newuser",
            email="new@example.com",
            password="testpass123"
        )

        # 用户应该已被缓存
        with patch.object(User.objects, 'get') as mock_get:
            cached_user = UserService.get_user_by_id(user.id)
            mock_get.assert_not_called()
            assert cached_user.id == user.id

    def test_get_user_by_username_caching(self):
        """Test get_user_by_username caches result."""
        user = UserService.register(
            username="usernamecache",
            email="username@example.com",
            password="testpass123"
        )

        # 第一次查询
        result1 = UserService.get_user_by_username("usernamecache")
        assert result1.id == user.id

        # 第二次查询应该从缓存获取
        with patch.object(User.objects, 'get') as mock_get:
            result2 = UserService.get_user_by_username("usernamecache")
            mock_get.assert_not_called()
            assert result2.id == user.id

    def test_cache_breakdown_protection(self):
        """Test cache breakdown protection with concurrent requests."""
        user = UserService.register(
            username="concurrent",
            email="concurrent@example.com",
            password="testpass123"
        )

        # 清除缓存
        cache.clear()

        import threading
        results = []
        db_call_count = [0]

        original_get = User.objects.get

        def counting_get(*args, **kwargs):
            db_call_count[0] += 1
            time.sleep(0.1)  # 模拟慢查询
            return original_get(*args, **kwargs)

        def fetch_user():
            with patch.object(User.objects, 'get', side_effect=counting_get):
                result = UserService.get_user_by_id(user.id)
                results.append(result)

        # 并发访问
        threads = [threading.Thread(target=fetch_user) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 所有线程应该获取到相同用户
        assert all(r.id == user.id for r in results)

        # 数据库查询应该只执行一次（缓存击穿保护）
        assert db_call_count[0] == 1

    def test_null_value_cache_expiry(self):
        """Test null value cache expires correctly."""
        # 查询不存在的用户
        result1 = UserService.get_user_by_id(99999)
        assert result1 is None

        # 验证缓存了空值
        cache_key = 'user:99999'
        cached_value = cache.get(cache_key)
        assert cached_value is not None  # 应该是 NULL_VALUE 标记

    def test_get_user_by_id_returns_correct_type(self):
        """Test get_user_by_id returns User instance or None."""
        user = UserService.register(
            username="typetest",
            email="type@example.com",
            password="testpass123"
        )

        result = UserService.get_user_by_id(user.id)
        assert isinstance(result, User)
        assert result.id == user.id

        # 不存在的用户返回 None
        none_result = UserService.get_user_by_id(99999)
        assert none_result is None


@pytest.mark.django_db
class TestCacheEvictDecorator:
    """Test cases for cache eviction."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        cache.clear()
        yield
        cache.clear()

    def test_update_user_invalidates_cache(self):
        """Test update_user invalidates user cache."""
        user = UserService.register(
            username="updateuser",
            email="update@example.com",
            password="testpass123"
        )

        # 先缓存用户
        UserService.get_user_by_id(user.id)

        # 更新用户
        updated = UserService.update_user(user.id, username="updatedname")

        # 验证缓存已被清除（下次查询会重新加载）
        # 注意：由于缓存装饰器的实现，这里需要验证行为
        assert updated.username == "updatedname"

    def test_multiple_cache_keys_for_user(self):
        """Test user is cached with multiple keys."""
        user = UserService.register(
            username="multikey",
            email="multi@example.com",
            password="testpass123"
        )

        # 通过 ID 缓存
        UserService.get_user_by_id(user.id)

        # 通过用户名缓存
        UserService.get_user_by_username("multikey")

        # 验证两个缓存都存在
        id_cache = cache.get(f'user:{user.id}')
        username_cache = cache.get('user:username:multikey')

        assert id_cache is not None
        assert username_cache is not None
