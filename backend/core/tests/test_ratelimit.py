"""Tests for ratelimit module."""
import pytest
import time
from unittest.mock import patch, MagicMock
from django.core.cache import cache
from core.ratelimit import (
    RateLimiter,
    RateLimitExceeded,
    rate_limit,
    rate_limit_by_ip,
    rate_limit_by_user,
    get_client_ip,
    add_rate_limit_headers
)


@pytest.fixture
def clear_cache():
    """Clear cache before each test."""
    cache.clear()
    yield
    cache.clear()


class TestRateLimiter:
    """Test cases for RateLimiter class."""

    def test_init_default_values(self):
        """Test RateLimiter initializes with default values."""
        limiter = RateLimiter()
        assert limiter.key_prefix == "ratelimit"
        assert limiter.max_requests == 100
        assert limiter.window_seconds == 60
        assert limiter.block_seconds is None

    def test_init_custom_values(self):
        """Test RateLimiter initializes with custom values."""
        limiter = RateLimiter(
            key_prefix="custom",
            max_requests=10,
            window_seconds=300,
            block_seconds=600
        )
        assert limiter.key_prefix == "custom"
        assert limiter.max_requests == 10
        assert limiter.window_seconds == 300
        assert limiter.block_seconds == 600

    def test_generate_key(self):
        """Test key generation with different configs."""
        limiter = RateLimiter()

        class MockConfig:
            method = "GET"
            url = "/api/test"
            params = {"page": 1}
            data = None

        key = limiter.generate_key(MockConfig())
        assert key == "GET_/api/test_{\"page\": 1}_null"

    def test_allow_request_within_limit(self, clear_cache):
        """Test request is allowed within rate limit."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)

        for i in range(5):
            allowed, info = limiter.allow_request("test_id")
            assert allowed is True
            assert info["allowed"] is True
            assert info["limit"] == 5
            assert info["current"] == i + 1

    def test_deny_request_over_limit(self, clear_cache):
        """Test request is denied when over rate limit."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)

        # 发送 3 个请求（达到上限）
        for _ in range(3):
            limiter.allow_request("test_id")

        # 第 4 个请求应该被拒绝
        allowed, info = limiter.allow_request("test_id")
        assert allowed is False
        assert info["allowed"] is False
        assert info["current"] == 3

    def test_block_after_limit(self, clear_cache):
        """Test blocking after exceeding limit."""
        limiter = RateLimiter(
            max_requests=2,
            window_seconds=60,
            block_seconds=300
        )

        # 发送 2 个请求
        limiter.allow_request("test_id")
        limiter.allow_request("test_id")

        # 第 3 个请求触发封禁
        allowed, info = limiter.allow_request("test_id")
        assert allowed is False
        assert info["blocked"] is True
        assert "retry_after" in info

        # 后续请求应该被拒绝（封禁状态）
        allowed, info = limiter.allow_request("test_id")
        assert allowed is False
        assert info["blocked"] is True

    def test_is_blocked_check(self, clear_cache):
        """Test is_blocked method."""
        limiter = RateLimiter(max_requests=1, block_seconds=60)

        assert limiter.is_blocked("test_id") is False

        limiter.allow_request("test_id")
        limiter.allow_request("test_id")  # 触发封禁

        assert limiter.is_blocked("test_id") is True


class TestRateLimitDecorator:
    """Test cases for rate_limit decorator."""

    def test_decorator_allows_request(self, clear_cache):
        """Test decorator allows requests within limit."""

        @rate_limit(max_requests=5, window_seconds=60)
        def test_view(request):
            return "success"

        mock_request = MagicMock()
        mock_request.META = {'REMOTE_ADDR': '127.0.0.1'}

        result = test_view(mock_request)
        assert result == "success"

    def test_decorator_blocks_request(self, clear_cache):
        """Test decorator blocks requests over limit."""

        @rate_limit(max_requests=2, window_seconds=60)
        def test_view(request):
            return "success"

        mock_request = MagicMock()
        mock_request.META = {'REMOTE_ADDR': '127.0.0.1'}

        # 前 2 个请求通过
        test_view(mock_request)
        test_view(mock_request)

        # 第 3 个请求应该被限流
        with pytest.raises(RateLimitExceeded):
            test_view(mock_request)

    def test_custom_key_function(self, clear_cache):
        """Test decorator with custom key function."""

        def custom_key(request):
            return f"custom:{request.user_id}"

        @rate_limit(key_func=custom_key, max_requests=1)
        def test_view(request):
            return "success"

        mock_request = MagicMock()
        mock_request.user_id = 123

        test_view(mock_request)

        # 相同 user_id 应该被限流
        with pytest.raises(RateLimitExceeded):
            test_view(mock_request)


class TestRateLimitByIP:
    """Test cases for rate_limit_by_ip decorator."""

    def test_limit_by_ip(self, clear_cache):
        """Test rate limiting by IP address."""

        @rate_limit_by_ip(max_requests=2, window_seconds=60)
        def test_view(request):
            return "success"

        mock_request = MagicMock()
        mock_request.META = {'REMOTE_ADDR': '192.168.1.1'}

        test_view(mock_request)
        test_view(mock_request)

        with pytest.raises(RateLimitExceeded):
            test_view(mock_request)

    def test_different_ips_not_affected(self, clear_cache):
        """Test different IPs have separate limits."""

        @rate_limit_by_ip(max_requests=1, window_seconds=60)
        def test_view(request):
            return "success"

        mock_request1 = MagicMock()
        mock_request1.META = {'REMOTE_ADDR': '192.168.1.1'}

        mock_request2 = MagicMock()
        mock_request2.META = {'REMOTE_ADDR': '192.168.1.2'}

        # 每个 IP 可以发送 1 个请求
        test_view(mock_request1)
        test_view(mock_request2)

        # 但同 IP 的第 2 个请求会被限流
        with pytest.raises(RateLimitExceeded):
            test_view(mock_request1)


class TestRateLimitByUser:
    """Test cases for rate_limit_by_user decorator."""

    def test_limit_by_authenticated_user(self, clear_cache):
        """Test rate limiting by authenticated user."""

        @rate_limit_by_user(max_requests=2, window_seconds=60)
        def test_view(request):
            return "success"

        mock_user = MagicMock()
        mock_user.id = 123

        mock_request = MagicMock()
        mock_request.auth = mock_user

        test_view(mock_request)
        test_view(mock_request)

        with pytest.raises(RateLimitExceeded):
            test_view(mock_request)

    def test_fallback_to_ip_for_anonymous(self, clear_cache):
        """Test fallback to IP for anonymous users."""

        @rate_limit_by_user(max_requests=1, window_seconds=60)
        def test_view(request):
            return "success"

        mock_request = MagicMock()
        mock_request.auth = None
        mock_request.META = {'REMOTE_ADDR': '192.168.1.1'}

        test_view(mock_request)

        with pytest.raises(RateLimitExceeded):
            test_view(mock_request)


class TestGetClientIP:
    """Test cases for get_client_ip function."""

    def test_get_ip_from_x_forwarded_for(self):
        """Test getting IP from X-Forwarded-For header."""
        mock_request = MagicMock()
        mock_request.META = {
            'HTTP_X_FORWARDED_FOR': '203.0.113.195, 70.41.3.18, 150.172.238.178'
        }

        ip = get_client_ip(mock_request)
        assert ip == '203.0.113.195'

    def test_get_ip_from_remote_addr(self):
        """Test getting IP from REMOTE_ADDR."""
        mock_request = MagicMock()
        mock_request.META = {
            'REMOTE_ADDR': '192.168.1.100'
        }

        ip = get_client_ip(mock_request)
        assert ip == '192.168.1.100'

    def test_get_ip_default_unknown(self):
        """Test default to 'unknown' when no IP found."""
        mock_request = MagicMock()
        mock_request.META = {}

        ip = get_client_ip(mock_request)
        assert ip == 'unknown'


class TestAddRateLimitHeaders:
    """Test cases for add_rate_limit_headers function."""

    def test_add_headers_to_response(self):
        """Test rate limit headers are added to response."""
        from django.http import JsonResponse

        response = JsonResponse({})
        info = {
            'limit': 100,
            'remaining': 50,
            'window': 60
        }

        result = add_rate_limit_headers(response, info)

        assert result['X-RateLimit-Limit'] == '100'
        assert result['X-RateLimit-Remaining'] == '50'
        assert result['X-RateLimit-Window'] == '60'

    def test_add_retry_after_header(self):
        """Test Retry-After header is added when retry_after present."""
        from django.http import JsonResponse

        response = JsonResponse({})
        info = {
            'limit': 100,
            'retry_after': 120
        }

        result = add_rate_limit_headers(response, info)

        assert result['Retry-After'] == '120'
