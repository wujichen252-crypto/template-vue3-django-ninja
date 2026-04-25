"""Performance tests for core modules."""
import pytest
import time
import threading
from unittest.mock import patch, MagicMock
from django.core.cache import cache
from core.cache import CacheManager, CacheStrategy, get_cache_manager
from core.ratelimit import RateLimiter


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before each test."""
    cache.clear()
    yield
    cache.clear()


class TestCachePerformance:
    """Performance tests for cache module."""

    def test_cache_read_performance(self):
        """Test cache read performance."""
        manager = CacheManager()

        # 预热缓存
        for i in range(100):
            manager.set(f'key_{i}', f'value_{i}')

        # 测试读取性能
        start = time.time()
        for i in range(1000):
            manager.get(f'key_{i % 100}')
        duration = time.time() - start

        # 1000 次读取应该在 1 秒内完成
        assert duration < 1.0

    def test_cache_write_performance(self):
        """Test cache write performance."""
        manager = CacheManager()

        start = time.time()
        for i in range(100):
            manager.set(f'perf_key_{i}', f'value_{i}')
        duration = time.time() - start

        # 100 次写入应该在 0.5 秒内完成
        assert duration < 0.5

    def test_concurrent_cache_access(self):
        """Test concurrent cache access performance."""
        manager = CacheManager()
        manager.set('concurrent_key', 'initial_value')

        results = []
        errors = []

        def access_cache():
            try:
                for _ in range(100):
                    value = manager.get('concurrent_key')
                    results.append(value)
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=access_cache) for _ in range(10)]
        start = time.time()

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        duration = time.time() - start

        # 1000 次并发读取应该在 2 秒内完成
        assert duration < 2.0
        assert len(errors) == 0
        assert len(results) == 1000

    def test_cache_with_jitter_performance(self):
        """Test cache with jitter doesn't impact performance."""
        strategy_with_jitter = CacheStrategy(jitter=True, timeout=60)
        strategy_without_jitter = CacheStrategy(jitter=False, timeout=60)

        manager_with = CacheManager(strategy_with_jitter)
        manager_without = CacheManager(strategy_without_jitter)

        # 测试带抖动的性能
        start = time.time()
        for i in range(100):
            manager_with.set(f'jitter_key_{i}', f'value_{i}')
        duration_with = time.time() - start

        # 测试不带抖动的性能
        start = time.time()
        for i in range(100):
            manager_without.set(f'no_jitter_key_{i}', f'value_{i}')
        duration_without = time.time() - start

        # 性能差异应该很小（小于 20%）
        assert abs(duration_with - duration_without) < duration_without * 0.2


class TestRateLimitPerformance:
    """Performance tests for rate limit module."""

    def test_rate_limit_check_performance(self):
        """Test rate limit check performance."""
        limiter = RateLimiter(max_requests=1000, window_seconds=60)

        start = time.time()
        for i in range(100):
            limiter.allow_request(f'user_{i}')
        duration = time.time() - start

        # 100 次不同用户的限流检查应该在 0.5 秒内完成
        assert duration < 0.5

    def test_rate_limit_same_user_performance(self):
        """Test rate limit check for same user."""
        limiter = RateLimiter(max_requests=10000, window_seconds=60)

        start = time.time()
        for _ in range(100):
            limiter.allow_request('same_user')
        duration = time.time() - start

        # 100 次同一用户的限流检查应该在 0.5 秒内完成
        assert duration < 0.5

    def test_concurrent_rate_limit_checks(self):
        """Test concurrent rate limit checks."""
        limiter = RateLimiter(max_requests=1000, window_seconds=60)
        results = []

        def check_limit():
            for i in range(50):
                allowed, _ = limiter.allow_request(f'concurrent_user_{i % 10}')
                results.append(allowed)

        threads = [threading.Thread(target=check_limit) for _ in range(5)]
        start = time.time()

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        duration = time.time() - start

        # 250 次并发限流检查应该在 2 秒内完成
        assert duration < 2.0
        assert len(results) == 250


class TestMemoryUsage:
    """Memory usage tests."""

    def test_cache_memory_efficiency(self):
        """Test cache memory efficiency with large data."""
        manager = CacheManager()

        # 存储大量数据
        large_data = 'x' * 10000  # 10KB
        for i in range(100):
            manager.set(f'large_key_{i}', large_data)

        # 验证可以正常读取
        for i in range(100):
            value = manager.get(f'large_key_{i}')
            assert value == large_data

    def test_cache_cleanup(self):
        """Test cache cleanup after expiry."""
        strategy = CacheStrategy(timeout=1)  # 1 秒过期
        manager = CacheManager(strategy)

        # 存储数据
        for i in range(50):
            manager.set(f'temp_key_{i}', f'value_{i}')

        # 等待过期
        time.sleep(1.5)

        # 数据应该已过期
        expired_count = 0
        for i in range(50):
            value = manager.get(f'temp_key_{i}')
            if value is None:
                expired_count += 1

        # 大部分数据应该已过期
        assert expired_count >= 45


class TestCacheStrategies:
    """Tests for different cache strategies."""

    def test_short_strategy_performance(self):
        """Test short cache strategy performance."""
        manager = get_cache_manager('short')

        start = time.time()
        for i in range(100):
            manager.set(f'short_key_{i}', f'value_{i}')
            manager.get(f'short_key_{i}')
        duration = time.time() - start

        assert duration < 1.0

    def test_long_strategy_performance(self):
        """Test long cache strategy performance."""
        manager = get_cache_manager('long')

        start = time.time()
        for i in range(100):
            manager.set(f'long_key_{i}', f'value_{i}')
            manager.get(f'long_key_{i}')
        duration = time.time() - start

        assert duration < 1.0


class TestBenchmark:
    """Benchmark tests."""

    @pytest.mark.benchmark
    def test_cache_get_benchmark(self):
        """Benchmark cache get operation."""
        manager = CacheManager()
        manager.set('benchmark_key', 'benchmark_value')

        iterations = 10000
        start = time.time()

        for _ in range(iterations):
            manager.get('benchmark_key')

        duration = time.time() - start
        ops_per_second = iterations / duration

        print(f"\nCache GET: {ops_per_second:.0f} ops/sec")
        assert ops_per_second > 10000  # 至少 10000 次/秒

    @pytest.mark.benchmark
    def test_rate_limit_benchmark(self):
        """Benchmark rate limit check."""
        limiter = RateLimiter(max_requests=100000, window_seconds=60)

        iterations = 10000
        start = time.time()

        for i in range(iterations):
            limiter.allow_request(f'benchmark_user_{i}')

        duration = time.time() - start
        ops_per_second = iterations / duration

        print(f"\nRate Limit Check: {ops_per_second:.0f} ops/sec")
        assert ops_per_second > 5000  # 至少 5000 次/秒
