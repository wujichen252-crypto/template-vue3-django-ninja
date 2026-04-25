"""API 限流模块

基于 Redis 有序集合（ZSET）的滑动窗口限流实现
"""
import time
import uuid
from functools import wraps
from typing import Optional, Callable
from django.core.cache import cache
from ninja.errors import HttpError


class RateLimitExceeded(HttpError):
    """限流异常"""
    def __init__(self, message: str = "请求过于频繁，请稍后再试"):
        super().__init__(status_code=429, message=message)


def _get_redis_connection():
    """获取 Redis 原生连接"""
    from django_redis import get_redis_connection
    return get_redis_connection("default")


class RateLimiter:
    """滑动窗口限流器

    使用 Redis 有序集合（ZSET）实现真正的分布式滑动窗口限流
    支持按 IP、用户、自定义 Key 限流
    """

    def __init__(
        self,
        key_prefix: str = "ratelimit",
        max_requests: int = 100,
        window_seconds: int = 60,
        block_seconds: Optional[int] = None
    ):
        """
        Args:
            key_prefix: Redis key 前缀
            max_requests: 时间窗口内最大请求数
            window_seconds: 时间窗口（秒）
            block_seconds: 触发限流后的封禁时间（秒），None 则不封禁
        """
        self.key_prefix = key_prefix
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.block_seconds = block_seconds

    def _get_key(self, identifier: str) -> str:
        """生成 Redis ZSET key"""
        return f"{self.key_prefix}:{identifier}"

    def _get_block_key(self, identifier: str) -> str:
        """生成封禁 key"""
        return f"{self.key_prefix}:block:{identifier}"

    def is_blocked(self, identifier: str) -> bool:
        """检查是否被封禁"""
        if not self.block_seconds:
            return False
        block_key = self._get_block_key(identifier)
        return cache.get(block_key) is not None

    def allow_request(self, identifier: str) -> tuple[bool, dict]:
        """检查是否允许请求（使用滑动窗口算法）

        Returns:
            (是否允许, 限流信息)
        """
        # 检查封禁状态
        if self.is_blocked(identifier):
            block_key = self._get_block_key(identifier)
            ttl = cache.ttl(block_key) or self.block_seconds
            return False, {
                "allowed": False,
                "blocked": True,
                "retry_after": ttl,
                "limit": self.max_requests,
                "window": self.window_seconds
            }

        key = self._get_key(identifier)
        now = time.time()
        window_start = now - self.window_seconds

        try:
            # 获取 Redis 原生连接
            redis_conn = _get_redis_connection()

            # 使用 Pipeline 保证原子性
            pipe = redis_conn.pipeline(True)
            
            # 1. 移除窗口外的请求记录
            pipe.zremrangebyscore(key, 0, window_start)
            
            # 2. 获取当前窗口内的请求数
            pipe.zcard(key)
            
            # 3. 设置 key 过期时间（自动清理）
            pipe.expire(key, self.window_seconds)
            
            # 执行管道命令
            results = pipe.execute()
            current_count = results[1]

            # 4. 检查是否超过限制
            if current_count >= self.max_requests:
                # 触发限流，设置封禁
                if self.block_seconds:
                    block_key = self._get_block_key(identifier)
                    cache.set(block_key, True, timeout=self.block_seconds)

                return False, {
                    "allowed": False,
                    "blocked": False,
                    "retry_after": self.window_seconds,
                    "limit": self.max_requests,
                    "window": self.window_seconds,
                    "current": current_count
                }

            # 5. 添加当前请求记录（使用唯一 member 避免冲突）
            member = f"{now}:{uuid.uuid4().hex[:8]}"
            redis_conn.zadd(key, {member: now})
            redis_conn.expire(key, self.window_seconds)

            return True, {
                "allowed": True,
                "limit": self.max_requests,
                "remaining": max(0, self.max_requests - current_count - 1),
                "window": self.window_seconds,
                "current": current_count + 1
            }

        except Exception as e:
            # Redis 异常时放行请求，避免影响正常业务
            from django.conf import settings
            if settings.DEBUG:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"限流检查失败: {e}")
            
            return True, {
                "allowed": True,
                "limit": self.max_requests,
                "remaining": self.max_requests,
                "window": self.window_seconds,
                "current": 0
            }


def rate_limit(
    key_func: Optional[Callable] = None,
    max_requests: int = 100,
    window_seconds: int = 60,
    block_seconds: Optional[int] = None,
    key_prefix: str = "ratelimit"
):
    """限流装饰器

    Args:
        key_func: 自定义 key 生成函数，接收 request 参数
        max_requests: 时间窗口内最大请求数
        window_seconds: 时间窗口（秒）
        block_seconds: 触发限流后的封禁时间
        key_prefix: Redis key 前缀
    """
    def decorator(func: Callable) -> Callable:
        limiter = RateLimiter(
            key_prefix=key_prefix,
            max_requests=max_requests,
            window_seconds=window_seconds,
            block_seconds=block_seconds
        )

        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # 生成限流标识
            if key_func:
                identifier = key_func(request)
            else:
                # 默认使用 IP + 用户 ID
                ip = get_client_ip(request)
                user_id = getattr(request, 'auth', None)
                if user_id:
                    identifier = f"user:{user_id}"
                else:
                    identifier = f"ip:{ip}"

            allowed, info = limiter.allow_request(identifier)

            # 设置响应头
            if hasattr(request, '_rate_limit_info'):
                request._rate_limit_info = info

            if not allowed:
                raise RateLimitExceeded()

            return func(request, *args, **kwargs)

        return wrapper
    return decorator


def rate_limit_by_ip(
    max_requests: int = 100,
    window_seconds: int = 60,
    block_seconds: Optional[int] = None
):
    """按 IP 限流装饰器"""
    def key_func(request):
        return f"ip:{get_client_ip(request)}"

    return rate_limit(
        key_func=key_func,
        max_requests=max_requests,
        window_seconds=window_seconds,
        block_seconds=block_seconds,
        key_prefix="ratelimit:ip"
    )


def rate_limit_by_user(
    max_requests: int = 1000,
    window_seconds: int = 60,
    block_seconds: Optional[int] = None
):
    """按用户限流装饰器"""
    def key_func(request):
        user = getattr(request, 'auth', None)
        if user:
            return f"user:{user.id}"
        # 未登录用户使用 IP
        return f"ip:{get_client_ip(request)}"

    return rate_limit(
        key_func=key_func,
        max_requests=max_requests,
        window_seconds=window_seconds,
        block_seconds=block_seconds,
        key_prefix="ratelimit:user"
    )


def get_client_ip(request) -> str:
    """获取客户端真实 IP"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', 'unknown')
    return ip


def add_rate_limit_headers(response, info: dict):
    """添加限流响应头"""
    response['X-RateLimit-Limit'] = str(info.get('limit', ''))
    response['X-RateLimit-Remaining'] = str(info.get('remaining', ''))
    response['X-RateLimit-Window'] = str(info.get('window', ''))
    if 'retry_after' in info:
        response['Retry-After'] = str(info['retry_after'])
    return response
