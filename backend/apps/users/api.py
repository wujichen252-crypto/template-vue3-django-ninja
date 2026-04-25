"""User API routes."""
from ninja import Router
from typing import List
from apps.users.schemas import RegisterIn, LoginIn, UserOut, TokenOut, RefreshTokenIn
from apps.users.services import UserService
from apps.users.models import User
from core.auth import JWTAuth
from core.response import StandardResponse
from core.ratelimit import rate_limit_by_ip, rate_limit_by_user, get_client_ip

router = Router(tags=['用户'])


def _get_request_id(request) -> str:
    """Get request_id from request object."""
    return getattr(request, 'request_id', '')


@router.post('/auth/register', response=StandardResponse[UserOut])
@rate_limit_by_ip(max_requests=5, window_seconds=3600, block_seconds=7200)
def register(request, payload: RegisterIn):
    """User registration endpoint.

    限流: 每小时每 IP 最多 5 次注册尝试，超限封禁 2 小时
    """
    user = UserService.register(
        username=payload.username,
        email=payload.email,
        password=payload.password
    )
    return StandardResponse(
        request_id=_get_request_id(request),
        data=UserOut(
            id=user.id,
            username=user.username,
            email=user.email,
            avatar_url=user.avatar_url,
            status=user.status,
            created_at=user.created_at
        )
    )


@router.post('/auth/login', response=StandardResponse[TokenOut])
@rate_limit_by_ip(max_requests=10, window_seconds=300, block_seconds=600)
def login(request, payload: LoginIn):
    """User login endpoint.

    限流: 每 5 分钟每 IP 最多 10 次登录尝试，超限封禁 10 分钟
    注意: 与登录失败锁定机制配合使用
    """
    tokens = UserService.authenticate(
        username=payload.username,
        password=payload.password
    )
    return StandardResponse(
        request_id=_get_request_id(request),
        data=TokenOut(**tokens)
    )


@router.get('/users/me', response=StandardResponse[UserOut], auth=JWTAuth())
@rate_limit_by_user(max_requests=100, window_seconds=60)
def get_current_user(request):
    """Get current authenticated user.

    限流: 每分钟每用户最多 100 次请求
    """
    user = request.auth
    if not user:
        return StandardResponse.error(code=401, msg='未授权')

    return StandardResponse(
        request_id=_get_request_id(request),
        data=UserOut(
            id=user.id,
            username=user.username,
            email=user.email,
            avatar_url=user.avatar_url,
            status=user.status,
            created_at=user.created_at
        )
    )


@router.post('/auth/refresh', response=StandardResponse[TokenOut])
@rate_limit_by_ip(max_requests=20, window_seconds=60)
def refresh_token(request, payload: RefreshTokenIn):
    """Refresh access token.

    限流: 每分钟每 IP 最多 20 次刷新请求
    """
    tokens = UserService.refresh_access_token(payload.refresh)
    return StandardResponse(
        request_id=_get_request_id(request),
        data=TokenOut(**tokens)
    )
