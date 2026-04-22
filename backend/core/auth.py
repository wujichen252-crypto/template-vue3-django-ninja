"""JWT authentication module."""
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from django.conf import settings
from ninja.security import HttpBearer
from apps.users.models import User
from core.exceptions import AuthorizationError
import logging

logger = logging.getLogger(__name__)


def generate_access_token(user_id: int) -> str:
    """Generate JWT access token (2 hours expiry)."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES)
    payload = {
        'user_id': user_id,
        'exp': expire,
        'type': 'access'
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256')


def generate_refresh_token(user_id: int) -> str:
    """Generate JWT refresh token (7 days expiry)."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)
    payload = {
        'user_id': user_id,
        'exp': expire,
        'type': 'refresh'
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256')


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and verify JWT token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthorizationError('令牌已过期')
    except jwt.InvalidTokenError:
        raise AuthorizationError('无效的令牌')


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
