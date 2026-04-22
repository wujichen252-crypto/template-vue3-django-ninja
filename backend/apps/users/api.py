"""User API routes."""
from ninja import Router
from typing import List
from apps.users.schemas import RegisterIn, LoginIn, UserOut, TokenOut, RefreshTokenIn
from apps.users.services import UserService
from apps.users.models import User
from core.auth import JWTAuth
from core.response import StandardResponse

router = Router(tags=['用户'])


def _get_request_id(request) -> str:
    """Get request_id from request object."""
    return getattr(request, 'request_id', '')


@router.post('/auth/register', response=StandardResponse[UserOut])
def register(request, payload: RegisterIn):
    """User registration endpoint."""
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
def login(request, payload: LoginIn):
    """User login endpoint."""
    tokens = UserService.authenticate(
        username=payload.username,
        password=payload.password
    )
    return StandardResponse(
        request_id=_get_request_id(request),
        data=TokenOut(**tokens)
    )


@router.get('/users/me', response=StandardResponse[UserOut], auth=JWTAuth())
def get_current_user(request):
    """Get current authenticated user."""
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
def refresh_token(request, payload: RefreshTokenIn):
    """Refresh access token."""
    tokens = UserService.refresh_access_token(payload.refresh)
    return StandardResponse(
        request_id=_get_request_id(request),
        data=TokenOut(**tokens)
    )
