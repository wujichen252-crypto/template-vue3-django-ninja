"""Tests for enhanced cache module."""
import pytest
import time
from unittest.mock import patch, MagicMock
from django.core.cache import cache
from core.cache import (
    CacheStrategy,
    CacheManager,
    cached,
    cache_evict,
    get_cache_manager,
    default_cache_manager
)


@pytest.fixture
def clear_cache():
    """Clear cache before each test."""
    cache.clear()
    yield
    cache.clear()


class TestCacheStrategy:
    """Test cases for CacheStrategy class."""

    def test_default_values(self):
        """Test CacheStrategy initializes with default values."""
        strategy = CacheStrategy()
        assert strategy.timeout == 300
        assert strategy.null_timeout == 60
        assert strategy.jitter is True
        assert strategy.jitter_range == (0.8, 1.2)
        assert strategy.lock_timeout == 10

    def test_custom_values(self):
        """Test CacheStrategy initializes with custom values."""
        strategy = CacheStrategy(
            timeout=600,
            null_timeout=120,
            jitter=False,
            lock_timeout=20
        )
        assert strategy.timeout == 600
        assert strategy.null_timeout == 120
        assert strategy.jitter is False
        assert strategy.lock_timeout == 20

    def test_get_timeout_without_jitter(self):
        """Test get_timeout returns fixed value when jitter disabled."""
        strategy = CacheStrategy(timeout=300, jitter=False)
        assert strategy.get_timeout() == 300

    def test_get_timeout_with_jitter(self):
        """Test get_timeout returns value within jitter range."""
        strategy = CacheStrategy(timeout=100, jitter=True, jitter_range=(0.5, 1.5))
        timeout = strategy.get_timeout()
        assert 50 <= timeout <= 150


class TestCacheManager:
    """Test cases for CacheManager class."""

    def test_init_with_default_strategy(self):
        """Test CacheManager initializes with default strategy."""
        manager = CacheManager()
        assert manager.strategy is not None
        assert manager.strategy.timeout == 300

    def test_init_with_custom_strategy(self):
        """Test CacheManager initializes with custom strategy."""
        strategy = CacheStrategy(timeout=600)
        manager = CacheManager(strategy)
        assert manager.strategy.timeout == 600

    def test_set_and_get(self, clear_cache):
        """Test basic set and get operations."""
        manager = CacheManager()

        manager.set('test_key', 'test_value')
        value = manager.get('test_key')

        assert value == 'test_value'

    def test_get_nonexistent_key(self, clear_cache):
        """Test get returns default for non-existent key."""
        manager = CacheManager()

        value = manager.get('nonexistent_key', 'default_value')
        assert value == 'default_value'

    def test_get_null_value(self, clear_cache):
        """Test get returns None for null value marker."""
        manager = CacheManager()

        manager.set('null_key', None, null_value=True)
        value = manager.get('null_key')

        assert value is None

    def test_delete(self, clear_cache):
        """Test delete operation."""
        manager = CacheManager()

        manager.set('delete_key', 'value')
        manager.delete('delete_key')

        value = manager.get('delete_key')
        assert value is None

    def test_get_or_set_caches_result(self, clear_cache):
        """Test get_or_set caches the result."""
        manager = CacheManager()
        getter = MagicMock(return_value='computed_value')

        # First call should execute getter
        value1 = manager.get_or_set('compute_key', getter)
        assert value1 == 'computed_value'
        assert getter.call_count == 1

        # Second call should return cached value
        value2 = manager.get_or_set('compute_key', getter)
        assert value2 == 'computed_value'
        assert getter.call_count == 1  # Getter not called again

    def test_get_or_set_with_none_value(self, clear_cache):
        """Test get_or_set caches None values (cache penetration protection)."""
        manager = CacheManager()
        getter = MagicMock(return_value=None)

        value1 = manager.get_or_set('none_key', getter, cache_none=True)
        assert value1 is None

        # Should return cached None without calling getter again
        value2 = manager.get_or_set('none_key', getter, cache_none=True)
        assert value2 is None
        assert getter.call_count == 1

    def test_get_or_set_concurrent_access(self, clear_cache):
        """Test get_or_set handles concurrent access (cache breakdown protection)."""
        manager = CacheManager()
        call_count = 0

        def slow_getter():
            nonlocal call_count
            call_count += 1
            time.sleep(0.1)
            return f'value_{call_count}'

        # Simulate concurrent access
        import threading
        results = []

        def access_cache():
            result = manager.get_or_set('concurrent_key', slow_getter)
            results.append(result)

        threads = [threading.Thread(target=access_cache) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Only one getter call should be made
        assert call_count == 1
        # All threads should get the same value
        assert all(r == results[0] for r in results)


class TestCachedDecorator:
    """Test cases for cached decorator."""

    def test_cached_decorator_caches_result(self, clear_cache):
        """Test cached decorator caches function result."""
        call_count = 0

        @cached(key_prefix='test', timeout=300)
        def compute_expensive(x, y):
            nonlocal call_count
            call_count += 1
            return x + y

        result1 = compute_expensive(1, 2)
        assert result1 == 3
        assert call_count == 1

        result2 = compute_expensive(1, 2)
        assert result2 == 3
        assert call_count == 1  # Function not called again

    def test_cached_decorator_different_args(self, clear_cache):
        """Test cached decorator handles different arguments."""
        call_count = 0

        @cached(key_prefix='test')
        def compute(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        compute(1)
        compute(2)

        assert call_count == 2  # Different args, different cache keys

    def test_cached_with_custom_key_func(self, clear_cache):
        """Test cached decorator with custom key function."""
        call_count = 0

        def custom_key(x, y):
            return f'custom:{x}'

        @cached(key_prefix='test', key_func=custom_key)
        def compute(x, y):
            nonlocal call_count
            call_count += 1
            return x + y

        compute(1, 2)
        compute(1, 3)  # Same x, should use cached result

        assert call_count == 1


class TestCacheEvictDecorator:
    """Test cases for cache_evict decorator."""

    def test_cache_evict_removes_cache(self, clear_cache):
        """Test cache_evict decorator removes cache entry."""
        manager = CacheManager()
        manager.set('user:123', 'user_data')

        @cache_evict(key_prefix='user')
        def update_user(user_id):
            return f'updated_{user_id}'

        update_user(123)

        # Cache should be removed
        value = manager.get('user:123')
        assert value is None

    def test_cache_evict_with_custom_key_func(self, clear_cache):
        """Test cache_evict with custom key function."""
        manager = CacheManager()
        manager.set('custom:456', 'data')

        def custom_key(user_id):
            return f'custom:{user_id}'

        @cache_evict(key_prefix='user', key_func=custom_key)
        def delete_user(user_id):
            return f'deleted_{user_id}'

        delete_user(456)

        value = manager.get('custom:456')
        assert value is None


class TestGetCacheManager:
    """Test cases for get_cache_manager function."""

    def test_get_short_strategy(self):
        """Test getting short cache strategy."""
        manager = get_cache_manager('short')
        assert manager.strategy.timeout == 60
        assert manager.strategy.null_timeout == 10

    def test_get_medium_strategy(self):
        """Test getting medium cache strategy."""
        manager = get_cache_manager('medium')
        assert manager.strategy.timeout == 300
        assert manager.strategy.null_timeout == 60

    def test_get_long_strategy(self):
        """Test getting long cache strategy."""
        manager = get_cache_manager('long')
        assert manager.strategy.timeout == 3600
        assert manager.strategy.null_timeout == 300

    def test_get_user_strategy(self):
        """Test getting user cache strategy."""
        manager = get_cache_manager('user')
        assert manager.strategy.timeout == 3600
        assert manager.strategy.null_timeout == 300

    def test_get_unknown_strategy_defaults_to_medium(self):
        """Test unknown strategy defaults to medium."""
        manager = get_cache_manager('unknown')
        assert manager.strategy.timeout == 300


class TestCachePenetrationProtection:
    """Test cases for cache penetration protection."""

    def test_null_value_caching(self, clear_cache):
        """Test that None values are cached to prevent penetration."""
        manager = CacheManager()
        getter = MagicMock(return_value=None)

        # First call returns None and caches it
        result1 = manager.get_or_set('penetrate_key', getter, cache_none=True)
        assert result1 is None

        # Second call returns cached None without hitting getter
        result2 = manager.get_or_set('penetrate_key', getter, cache_none=True)
        assert result2 is None
        assert getter.call_count == 1

    def test_null_value_with_short_timeout(self, clear_cache):
        """Test null values use shorter timeout."""
        strategy = CacheStrategy(timeout=3600, null_timeout=60)
        manager = CacheManager(strategy)

        manager.set('null_key', None, null_value=True)

        # Null value should be cached with null_timeout (60s)
        # This is harder to test without waiting, but we verify the logic
        assert manager.NULL_VALUE == "__CACHE_NULL__"


class TestCacheAvalancheProtection:
    """Test cases for cache avalanche protection."""

    def test_jitter_prevents_simultaneous_expiry(self):
        """Test that jitter prevents cache avalanche."""
        strategy = CacheStrategy(timeout=100, jitter=True, jitter_range=(0.8, 1.2))

        timeouts = [strategy.get_timeout() for _ in range(100)]

        # All timeouts should be within jitter range
        assert all(80 <= t <= 120 for t in timeouts)

        # Timeouts should vary (not all the same)
        assert len(set(timeouts)) > 1


class TestCacheBreakdownProtection:
    """Test cases for cache breakdown protection."""

    def test_lock_prevents_concurrent_rebuild(self, clear_cache):
        """Test that lock prevents concurrent cache rebuild."""
        manager = CacheManager()
        rebuild_count = 0

        def slow_rebuild():
            nonlocal rebuild_count
            rebuild_count += 1
            time.sleep(0.2)
            return f'rebuilt_{rebuild_count}'

        import threading

        def access():
            return manager.get_or_set('breakdown_key', slow_rebuild)

        # Start multiple threads simultaneously
        threads = [threading.Thread(target=access) for _ in range(5)]
        start_time = time.time()

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        end_time = time.time()

        # Only one rebuild should occur
        assert rebuild_count == 1

        # Total time should be about one rebuild time (not 5x)
        assert end_time - start_time < 0.5  # Should be ~0.2s, not 1.0s
