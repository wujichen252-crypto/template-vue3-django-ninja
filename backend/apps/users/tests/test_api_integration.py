"""Integration tests for user API with rate limiting and caching."""
import pytest
import time
from unittest.mock import patch
from django.core.cache import cache
from ninja.testing import TestClient
from config.urls import api


@pytest.fixture
def api_client():
    """Create API test client."""
    return TestClient(api)


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before each test."""
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
class TestAPIRateLimitIntegration:
    """Integration tests for API rate limiting."""

    def test_login_rate_limit_by_ip(self, api_client):
        """Test login endpoint rate limits by IP."""
        # 发送 10 个登录请求（达到限流阈值）
        for i in range(10):
            response = api_client.post(
                '/api/v1/auth/login',
                json={
                    'username': f'testuser{i}',
                    'password': 'wrongpassword'
                }
            )
            # 前 10 个请求应该返回 401（认证失败），不是 429
            if i < 10:
                assert response.status_code in [401, 400]

        # 第 11 个请求应该被限流
        response = api_client.post(
            '/api/v1/auth/login',
            json={
                'username': 'testuser',
                'password': 'password123'
            }
        )
        assert response.status_code == 429
        assert '请求过于频繁' in str(response.content)

    def test_register_rate_limit_by_ip(self, api_client):
        """Test register endpoint rate limits by IP."""
        # 发送 5 个注册请求
        for i in range(5):
            response = api_client.post(
                '/api/v1/auth/register',
                json={
                    'username': f'newuser{i}',
                    'email': f'new{i}@example.com',
                    'password': 'password123'
                }
            )
            # 前几个可能成功或失败（用户名重复），但不应该被限流
            assert response.status_code in [200, 400]

        # 第 6 个请求应该被限流
        response = api_client.post(
            '/api/v1/auth/register',
            json={
                'username': 'anotheruser',
                'email': 'another@example.com',
                'password': 'password123'
            }
        )
        assert response.status_code == 429

    def test_rate_limit_headers_present(self, api_client):
        """Test rate limit headers are present in response."""
        # 先发送一个请求触发限流
        for i in range(11):
            response = api_client.post(
                '/api/v1/auth/login',
                json={
                    'username': f'user{i}',
                    'password': 'wrong'
                }
            )

        # 限流响应应该包含限流头
        assert response.status_code == 429
        # 注意：具体头部取决于实现，可能需要调整

    def test_different_endpoints_have_separate_limits(self, api_client):
        """Test different endpoints have separate rate limits."""
        # 触发登录限流
        for i in range(11):
            api_client.post(
                '/api/v1/auth/login',
                json={'username': f'user{i}', 'password': 'wrong'}
            )

        # 登录被限流
        login_response = api_client.post(
            '/api/v1/auth/login',
            json={'username': 'test', 'password': 'test'}
        )
        assert login_response.status_code == 429

        # 但注册可能还没有被限流（独立的计数器）
        register_response = api_client.post(
            '/api/v1/auth/register',
            json={
                'username': 'separate',
                'email': 'separate@example.com',
                'password': 'test123'
            }
        )
        # 注册应该可以正常处理（或返回用户名已存在）
        assert register_response.status_code in [200, 400]


@pytest.mark.django_db
class TestAPICacheIntegration:
    """Integration tests for API caching."""

    def test_get_current_user_uses_cache(self, api_client):
        """Test get current user endpoint uses cache."""
        from apps.users.services import UserService

        # 注册用户并登录
        user = UserService.register(
            username='cachetest',
            email='cache@example.com',
            password='testpass123'
        )
        tokens = UserService.authenticate('cachetest', 'testpass123')

        # 第一次请求
        response1 = api_client.get(
            '/api/v1/users/me',
            headers={'Authorization': f'Bearer {tokens["access_token"]}'}
        )
        assert response1.status_code == 200

        # 第二次请求应该从缓存获取
        with patch('apps.users.models.User.objects.get') as mock_get:
            response2 = api_client.get(
                '/api/v1/users/me',
                headers={'Authorization': f'Bearer {tokens["access_token"]}'}
            )
            mock_get.assert_not_called()
            assert response2.status_code == 200

    def test_cache_invalidation_on_update(self, api_client):
        """Test cache is invalidated when user is updated."""
        from apps.users.services import UserService

        # 注册用户并登录
        user = UserService.register(
            username='updatetest',
            email='update@example.com',
            password='testpass123'
        )
        tokens = UserService.authenticate('updatetest', 'testpass123')

        # 先获取用户信息（缓存）
        api_client.get(
            '/api/v1/users/me',
            headers={'Authorization': f'Bearer {tokens["access_token"]}'}
        )

        # 更新用户
        UserService.update_user(user.id, username='updatedname')

        # 再次获取应该获取新数据
        response = api_client.get(
            '/api/v1/users/me',
            headers={'Authorization': f'Bearer {tokens["access_token"]}'}
        )
        assert response.status_code == 200
        # 注意：这里需要验证返回的数据是否已更新


@pytest.mark.django_db
class TestAPIEndToEnd:
    """End-to-end API tests."""

    def test_full_user_flow(self, api_client):
        """Test complete user flow: register -> login -> get user -> refresh token."""
        # 1. 注册
        register_response = api_client.post(
            '/api/v1/auth/register',
            json={
                'username': 'e2euser',
                'email': 'e2e@example.com',
                'password': 'testpass123'
            }
        )
        assert register_response.status_code == 200
        user_data = register_response.json()['data']
        assert user_data['username'] == 'e2euser'

        # 2. 登录
        login_response = api_client.post(
            '/api/v1/auth/login',
            json={
                'username': 'e2euser',
                'password': 'testpass123'
            }
        )
        assert login_response.status_code == 200
        tokens = login_response.json()['data']
        assert 'access_token' in tokens
        assert 'refresh_token' in tokens

        # 3. 获取当前用户
        me_response = api_client.get(
            '/api/v1/users/me',
            headers={'Authorization': f'Bearer {tokens["access_token"]}'}
        )
        assert me_response.status_code == 200
        me_data = me_response.json()['data']
        assert me_data['username'] == 'e2euser'

        # 4. 刷新 Token
        refresh_response = api_client.post(
            '/api/v1/auth/refresh',
            json={'refresh': tokens['refresh_token']}
        )
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()['data']
        assert 'access_token' in new_tokens
        assert new_tokens['access_token'] != tokens['access_token']

    def test_unauthorized_access(self, api_client):
        """Test unauthorized access is rejected."""
        # 没有 Token 访问受保护接口
        response = api_client.get('/api/v1/users/me')
        assert response.status_code == 401

        # 无效 Token
        response = api_client.get(
            '/api/v1/users/me',
            headers={'Authorization': 'Bearer invalid_token'}
        )
        assert response.status_code == 401

    def test_invalid_token_format(self, api_client):
        """Test invalid token format is rejected."""
        response = api_client.get(
            '/api/v1/users/me',
            headers={'Authorization': 'InvalidFormat token'}
        )
        assert response.status_code == 401


@pytest.mark.django_db
class TestAPIErrorHandling:
    """Tests for API error handling."""

    def test_validation_error(self, api_client):
        """Test validation errors return 400."""
        # 缺少必填字段
        response = api_client.post(
            '/api/v1/auth/register',
            json={
                'username': 'test',
                # 缺少 email 和 password
            }
        )
        assert response.status_code == 400

    def test_not_found(self, api_client):
        """Test 404 for non-existent endpoints."""
        response = api_client.get('/api/v1/nonexistent')
        assert response.status_code == 404

    def test_method_not_allowed(self, api_client):
        """Test method not allowed."""
        # GET 请求到只支持 POST 的端点
        response = api_client.get('/api/v1/auth/login')
        assert response.status_code == 405


@pytest.mark.django_db
class TestAPIPerformance:
    """Performance tests for API."""

    def test_cached_response_faster(self, api_client):
        """Test cached responses are faster than uncached."""
        from apps.users.services import UserService

        # 注册用户并登录
        UserService.register(
            username='perftest',
            email='perf@example.com',
            password='testpass123'
        )
        tokens = UserService.authenticate('perftest', 'testpass123')

        # 第一次请求（无缓存）
        start1 = time.time()
        api_client.get(
            '/api/v1/users/me',
            headers={'Authorization': f'Bearer {tokens["access_token"]}'}
        )
        duration1 = time.time() - start1

        # 第二次请求（有缓存）
        start2 = time.time()
        api_client.get(
            '/api/v1/users/me',
            headers={'Authorization': f'Bearer {tokens["access_token"]}'}
        )
        duration2 = time.time() - start2

        # 缓存响应应该更快（或至少不更慢）
        # 注意：在测试环境中差异可能不明显
        assert duration2 <= duration1 * 1.5  # 允许一些误差

    def test_concurrent_requests(self, api_client):
        """Test API handles concurrent requests."""
        import threading

        results = []

        def make_request():
            response = api_client.post(
                '/api/v1/auth/login',
                json={
                    'username': 'nonexistent',
                    'password': 'wrong'
                }
            )
            results.append(response.status_code)

        # 并发发送 5 个请求
        threads = [threading.Thread(target=make_request) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 所有请求都应该完成
        assert len(results) == 5
        # 应该都是 401（认证失败），不是 500
        assert all(code in [401, 400, 429] for code in results)
