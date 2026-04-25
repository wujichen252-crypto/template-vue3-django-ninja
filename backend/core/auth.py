"""JWT authentication module."""
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from django.conf import settings
from django.core.cache import cache
from ninja.security import HttpBearer
from apps.users.models import User
from core.exceptions import AuthorizationError
import logging

logger = logging.getLogger(__name__)


# Token 黑名单 Redis key 前缀
TOKEN_BLACKLIST_PREFIX = 'token:blacklist'


def generate_access_token(user_id: int) -> str:
    """Generate JWT access token (2 hours expiry)."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES)
    payload = {
        'user_id': user_id,
        'exp': expire,
        'type': 'access',
        'jti': f'{user_id}:{expire.timestamp()}'  # 唯一标识
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256')


def generate_refresh_token(user_id: int) -> str:
    """Generate JWT refresh token (7 days expiry)."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)
    payload = {
        'user_id': user_id,
        'exp': expire,
        'type': 'refresh',
        'jti': f'{user_id}:{expire.timestamp()}'  # 唯一标识
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256')


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and verify JWT token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=['HS256'])
        
        # 检查是否在黑名单中
        if is_token_blacklisted(token):
            raise AuthorizationError('令牌已失效')
        
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthorizationError('令牌已过期')
    except jwt.InvalidTokenError:
        raise AuthorizationError('无效的令牌')


def blacklist_token(token: str, expire_seconds: Optional[int] = None) -> bool:
    """将 Token 加入黑名单
    
    Args:
        token: JWT token
        expire_seconds: 黑名单过期时间（秒），默认使用 token 剩余有效期
    
    Returns:
        是否成功加入黑名单
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=['HS256'], options={'verify_exp': False})
        exp = payload.get('exp')
        
        if not expire_seconds:
            expire_seconds = int(exp - datetime.now(timezone.utc).timestamp())
            if expire_seconds <= 0:
                return True
        
        blacklist_key = f'{TOKEN_BLACKLIST_PREFIX}:{token[:16]}'
        cache.set(blacklist_key, True, timeout=expire_seconds)
        
        logger.info(f"Token 已加入黑名单，过期时间: {expire_seconds}s")
        return True
    except Exception as e:
        logger.error(f"加入 Token 黑名单失败: {e}")
        return False


def is_token_blacklisted(token: str) -> bool:
    """检查 Token 是否在黑名单中"""
    blacklist_key = f'{TOKEN_BLACKLIST_PREFIX}:{token[:16]}'
    return cache.get(blacklist_key) is not None


class JWTAuth(HttpBearer):
    """JWT authentication class for Ninja."""

    def __init__(self):
        super().__init__()

    def authenticate(self, request, bearer: str) -> Optional[User]:
        if not bearer:
            return None

        try:
            payload = decode_token(bearer)
            if payload.get('type') != 'access':
                return None

            user_id = payload.get('user_id')
            if not user_id:
                return None

            from apps.users.services import UserService
            user = UserService.get_user_by_id(user_id)
            return user
        except AuthorizationError:
            raise
        except Exception as e:
            logger.error(f"JWT认证失败: {str(e)}")
            return None
