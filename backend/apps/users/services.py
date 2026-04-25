"""User service layer."""
import bcrypt
from django.core.cache import cache
from typing import Optional
from apps.users.models import User
from core.auth import generate_access_token, generate_refresh_token, decode_token, blacklist_token
from core.exceptions import AuthenticationError
from core.cache import cached, cache_evict, get_cache_manager

# 用户缓存管理器（带防穿透、防雪崩、防击穿）
user_cache = get_cache_manager('user')


class UserService:
    """User business logic service."""

    LOGIN_MAX_ATTEMPTS = 5
    LOGIN_LOCKOUT_SECONDS = 300

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    @classmethod
    def register(cls, username: str, email: str, password: str) -> User:
        """Register a new user."""
        if User.objects.filter(username=username).exists():
            raise ValueError('用户名已存在')
        if User.objects.filter(email=email).exists():
            raise ValueError('邮箱已被注册')

        hashed_password = cls.hash_password(password)
        user = User.objects.create_user(
            username=username,
            email=email,
            password=hashed_password
        )
        # 新用户注册后，预热缓存
        cls._warm_user_cache(user)
        return user

    @classmethod
    def authenticate(cls, username: str, password: str) -> dict:
        """Authenticate user and generate tokens."""
        lockout_key = f'login_lockout:{username}'
        if cache.get(lockout_key):
            raise AuthenticationError('登录尝试次数过多，请5分钟后再试')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            cls._increase_login_attempts(username)
            raise AuthenticationError('用户名或密码错误')

        if user.status != User.STATUS_NORMAL:
            raise AuthenticationError('账号已被禁用')

        if not cls.verify_password(password, user.password):
            cls._increase_login_attempts(username)
            raise AuthenticationError('用户名或密码错误')

        cache.delete(lockout_key)
        access_token = generate_access_token(user.id)
        refresh_token = generate_refresh_token(user.id)

        # 登录成功后预热用户缓存
        cls._warm_user_cache(user)

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': 7200,
        }

    @classmethod
    def _increase_login_attempts(cls, username: str) -> None:
        """Increase login attempts counter and set lockout if threshold reached."""
        attempt_key = f'login_attempt:{username}'
        attempts = cache.get(attempt_key, 0) + 1
        cache.set(attempt_key, attempts, timeout=cls.LOGIN_LOCKOUT_SECONDS)
        if attempts >= cls.LOGIN_MAX_ATTEMPTS:
            cache.set(f'login_lockout:{username}', True, timeout=cls.LOGIN_LOCKOUT_SECONDS)

    @classmethod
    def get_user_by_id(cls, user_id: int) -> Optional[User]:
        """Get user by ID with enhanced Redis cache.

        使用增强型缓存，包含:
        - 缓存穿透防护（空值缓存）
        - 缓存雪崩防护（随机过期时间）
        - 缓存击穿防护（互斥锁）
        """
        cache_key = f'user:{user_id}'

        def fetch_user():
            try:
                return User.objects.get(id=user_id)
            except User.DoesNotExist:
                return None

        return user_cache.get_or_set(
            cache_key,
            fetch_user,
            timeout=3600,
            cache_none=True  # 缓存空值防穿透
        )

    @classmethod
    def _warm_user_cache(cls, user: User) -> None:
        """预热用户缓存"""
        cache_key = f'user:{user.id}'
        user_cache.set(cache_key, user, timeout=3600)

    @classmethod
    def _invalidate_user_cache(cls, user_id: int) -> None:
        """Invalidate user cache when user data is updated."""
        cache_key = f'user:{user_id}'
        user_cache.delete(cache_key)

    @classmethod
    def get_user_from_token(cls, token: str) -> Optional[User]:
        """Get user from JWT token."""
        try:
            payload = decode_token(token)
            user_id = payload.get('user_id')
            if not user_id:
                return None
            return cls.get_user_by_id(user_id)
        except ValueError:
            return None
        except Exception:
            return None

    @classmethod
    def refresh_access_token(cls, refresh_token: str) -> dict:
        """Refresh access token using refresh token."""
        payload = decode_token(refresh_token)

        if payload.get('type') != 'refresh':
            raise AuthenticationError('无效的刷新令牌')

        user_id = payload.get('user_id')
        if not user_id:
            raise AuthenticationError('无效的刷新令牌')

        user = cls.get_user_by_id(user_id)
        if not user:
            raise AuthenticationError('用户不存在')

        access_token = generate_access_token(user.id)
        new_refresh_token = generate_refresh_token(user.id)

        return {
            'access_token': access_token,
            'refresh_token': new_refresh_token,
            'expires_in': 7200,
        }

    @classmethod
    @cache_evict(key_prefix='user', key_func=lambda user_id: f'user:{user_id}')
    def update_user(cls, user_id: int, **kwargs) -> User:
        """Update user info and invalidate cache."""
        user = User.objects.get(id=user_id)
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        user.save()
        return user

    @classmethod
    def get_user_by_username(cls, username: str) -> Optional[User]:
        """Get user by username with cache."""
        cache_key = f'user:username:{username}'

        def fetch_user():
            try:
                return User.objects.get(username=username)
            except User.DoesNotExist:
                return None

        return user_cache.get_or_set(
            cache_key,
            fetch_user,
            timeout=1800,  # 30分钟
            cache_none=True
        )
