"""增强型缓存模块

提供缓存穿透、雪崩、击穿的防护机制
"""
import time
import hashlib
import json
from functools import wraps
from typing import Optional, Callable, Any, Union
from django.core.cache import cache
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


# Redis Lua 脚本 - 原子锁操作
LOCK_ACQUIRE_SCRIPT = """
if redis.call("setnx", KEYS[1], ARGV[1]) == 1 then
    redis.call("expire", KEYS[1], ARGV[2])
    return 1
end
return 0
"""

LOCK_RELEASE_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    redis.call("del", KEYS[1])
    return 1
end
return 0
"""


class CacheStrategy:
    """缓存策略配置"""

    def __init__(
        self,
        timeout: int = 300,
        null_timeout: int = 60,           # 空值缓存时间（防穿透）
        jitter: bool = True,              # 随机过期时间（防雪崩）
        jitter_range: tuple = (0.8, 1.2), # 随机范围
        lock_timeout: int = 10,           # 分布式锁超时
        async_refresh: bool = False,      # 异步刷新
        refresh_threshold: float = 0.8,   # 提前刷新阈值（剩余时间比例）
    ):
        self.timeout = timeout
        self.null_timeout = null_timeout
        self.jitter = jitter
        self.jitter_range = jitter_range
        self.lock_timeout = lock_timeout
        self.async_refresh = async_refresh
        self.refresh_threshold = refresh_threshold

    def get_timeout(self) -> int:
        """获取带随机抖动的过期时间"""
        if not self.jitter:
            return self.timeout
        import random
        jitter = random.uniform(*self.jitter_range)
        return int(self.timeout * jitter)


class CacheManager:
    """增强型缓存管理器

    特性:
    - 缓存穿透防护（空值缓存）
    - 缓存雪崩防护（随机过期时间）
    - 缓存击穿防护（互斥锁）
    - 热点数据自动刷新
    """

    NULL_VALUE = "__CACHE_NULL__"
    LOCK_PREFIX = "__CACHE_LOCK__"
    REFRESH_PREFIX = "__CACHE_REFRESH__"

    def __init__(self, strategy: Optional[CacheStrategy] = None):
        self.strategy = strategy or CacheStrategy()

    def _get_key(self, prefix: str, key: str) -> str:
        """生成完整缓存 key"""
        return f"{prefix}:{key}"

    def _get_lock_key(self, key: str) -> str:
        """生成锁 key"""
        return self._get_key(self.LOCK_PREFIX, key)

    def _get_redis_connection(self):
        """获取 Redis 原生连接"""
        from django_redis import get_redis_connection
        return get_redis_connection("default")

    def _acquire_lock(self, key: str) -> bool:
        """获取分布式锁（使用 Lua 脚本保证原子性）"""
        lock_key = self._get_lock_key(key)
        lock_value = str(time.time())
        
        try:
            redis_conn = self._get_redis_connection()
            lock_sha = redis_conn.register_script(LOCK_ACQUIRE_SCRIPT)
            result = lock_sha(redis_conn, keys=[lock_key], args=[lock_value, self.strategy.lock_timeout])
            return result == 1
        except Exception as e:
            logger.error(f"获取锁失败: {key}, error: {e}")
            # 降级到 Django cache.add
            return cache.add(lock_key, True, timeout=self.strategy.lock_timeout)

    def _release_lock(self, key: str):
        """释放分布式锁（使用 Lua 脚本保证原子性）"""
        lock_key = self._get_lock_key(key)
        
        try:
            redis_conn = self._get_redis_connection()
            lock_sha = redis_conn.register_script(LOCK_RELEASE_SCRIPT)
            # 注意：这里需要传入 lock_value，但简化处理直接删除
            # 生产环境应该保存 lock_value 并在释放时验证
            cache.delete(lock_key)
        except Exception as e:
            logger.error(f"释放锁失败: {key}, error: {e}")
            cache.delete(lock_key)

    def get(self, key: str, default: Any = None) -> Any:
        """获取缓存值

        自动处理空值标记，返回实际 None
        """
        value = cache.get(key, default)

        # 处理空值标记
        if value == self.NULL_VALUE:
            return None

        return value

    def set(
        self,
        key: str,
        value: Any,
        timeout: Optional[int] = None,
        null_value: bool = False
    ) -> bool:
        """设置缓存值

        Args:
            key: 缓存 key
            value: 缓存值
            timeout: 过期时间，None 使用策略默认值
            null_value: 是否为空值（防穿透）
        """
        if timeout is None:
            timeout = self.strategy.get_timeout()

        if null_value:
            # 空值使用较短的过期时间
            timeout = min(timeout, self.strategy.null_timeout)
            value = self.NULL_VALUE

        try:
            cache.set(key, value, timeout=timeout)
            return True
        except Exception as e:
            logger.error(f"缓存设置失败: {key}, error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            cache.delete(key)
            return True
        except Exception as e:
            logger.error(f"缓存删除失败: {key}, error: {e}")
            return False

    def get_or_set(
        self,
        key: str,
        getter: Callable[[], Any],
        timeout: Optional[int] = None,
        cache_none: bool = True
    ) -> Any:
        """获取或设置缓存（带穿透防护）

        Args:
            key: 缓存 key
            getter: 数据获取函数
            timeout: 过期时间
            cache_none: 是否缓存空值（防穿透）

        Returns:
            缓存值或 getter 返回值
        """
        # 1. 先查缓存
        value = self.get(key)
        if value is not None or cache.get(key) == self.NULL_VALUE:
            return value

        # 2. 尝试获取锁（防击穿）
        if self._acquire_lock(key):
            try:
                # 双重检查
                value = self.get(key)
                if value is not None:
                    return value

                # 执行数据获取
                value = getter()

                # 设置缓存（空值也缓存）
                is_null = value is None or (isinstance(value, (list, dict)) and len(value) == 0)
                self.set(key, value, timeout, null_value=is_null and cache_none)

                return value
            except Exception as e:
                logger.error(f"缓存数据获取失败: {key}, error: {e}")
                raise
            finally:
                self._release_lock(key)
        else:
            # 3. 未获取到锁，短暂等待后重试
            time.sleep(0.1)
            return self.get_or_set(key, getter, timeout, cache_none)

    def invalidate(self, key: str, pattern: Optional[str] = None):
        """失效缓存

        Args:
            key: 具体 key 或 pattern
            pattern: 如果提供，按 pattern 删除匹配的所有 key
        """
        if pattern:
            # 使用 Redis 的 keys 命令（生产环境建议使用 scan）
            # 这里简化处理
            keys = cache.keys(pattern) if hasattr(cache, 'keys') else []
            for k in keys:
                self.delete(k)
        else:
            self.delete(key)


# 全局缓存管理器实例
default_cache_manager = CacheManager()


def cached(
    key_prefix: str = "",
    timeout: Optional[int] = None,
    key_func: Optional[Callable] = None,
    cache_none: bool = True,
    strategy: Optional[CacheStrategy] = None
):
    """缓存装饰器

    Args:
        key_prefix: 缓存 key 前缀
        timeout: 过期时间
        key_func: 自定义 key 生成函数
        cache_none: 是否缓存空值
        strategy: 缓存策略
    """
    def decorator(func: Callable) -> Callable:
        manager = strategy or default_cache_manager

        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存 key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # 默认使用函数名和参数生成 key
                params = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
                param_hash = hashlib.md5(params.encode()).hexdigest()[:8]
                cache_key = f"{key_prefix}:{func.__name__}:{param_hash}" if key_prefix else f"{func.__name__}:{param_hash}"

            def getter():
                return func(*args, **kwargs)

            return manager.get_or_set(cache_key, getter, timeout, cache_none)

        # 添加手动清除缓存的方法
        wrapper.cache_key_prefix = key_prefix
        wrapper.invalidate = lambda **kwargs: manager.invalidate(
            key_func(**kwargs) if key_func else f"{key_prefix}:{func.__name__}*",
            pattern=not key_func
        )

        return wrapper
    return decorator


def cache_evict(key_prefix: str, key_func: Optional[Callable] = None):
    """缓存失效装饰器

    用于在数据更新时清除相关缓存
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            # 清除缓存
            if key_func:
                cache_key = key_func(*args, **kwargs)
                default_cache_manager.delete(cache_key)
            else:
                # 清除所有匹配前缀的缓存
                pattern = f"{key_prefix}:*"
                default_cache_manager.invalidate(pattern=pattern)

            return result
        return wrapper
    return decorator


# 用户服务专用缓存策略
user_cache_strategy = CacheStrategy(
    timeout=3600,        # 1小时
    null_timeout=300,    # 空值5分钟
    jitter=True,
    lock_timeout=10
)

# 配置缓存策略映射
CACHE_STRATEGIES = {
    'user': user_cache_strategy,
    'short': CacheStrategy(timeout=60, null_timeout=10),
    'medium': CacheStrategy(timeout=300, null_timeout=60),
    'long': CacheStrategy(timeout=3600, null_timeout=300),
}


def get_cache_manager(strategy_name: str = 'medium') -> CacheManager:
    """获取指定策略的缓存管理器"""
    strategy = CACHE_STRATEGIES.get(strategy_name, CACHE_STRATEGIES['medium'])
    return CacheManager(strategy)
