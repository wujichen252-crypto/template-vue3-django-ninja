"""User service layer."""
import bcrypt
from django.core.cache import cache
from typing import Optional
from apps.users.models import User
from core.auth import generate_access_token, generate_refresh_token, decode_token
from core.exceptions import AuthenticationError


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
        cls._invalidate_user_cache(user.id)
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
        """Get user by ID with Redis cache."""
        cache_key = f'user:{user_id}'
        cached_user = cache.get(cache_key)

        if cached_user:
            return cached_user

        try:
            user = User.objects.get(id=user_id)
            cache.set(cache_key, user, timeout=3600)
            return user
        except User.DoesNotExist:
            return None

    @classmethod
    def _invalidate_user_cache(cls, user_id: int) -> None:
        """Invalidate user cache when user data is updated."""
        cache_key = f'user:{user_id}'
        cache.delete(cache_key)

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
