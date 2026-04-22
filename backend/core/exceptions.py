"""Core exceptions module."""


class AuthenticationError(ValueError):
    """认证失败异常."""
    pass


class AuthorizationError(ValueError):
    """授权失败异常."""
    pass


"""Global exception handlers for Ninja API."""
from ninja import NinjaAPI
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpRequest
from pydantic import ValidationError as PydanticValidationError
from core.response import StandardResponse
from core.exceptions import AuthenticationError, AuthorizationError


def register_exception_handlers(api: NinjaAPI):
    """Register global exception handlers."""

    @api.exception_handler(ValidationError)
    def validation_error_handler(request: HttpRequest, exc: ValidationError):
        return StandardResponse.error(code=400, msg='数据验证失败')

    @api.exception_handler(PydanticValidationError)
    def pydantic_validation_error_handler(request: HttpRequest, exc: PydanticValidationError):
        errors = exc.errors()
        error_msg = '; '.join([f"{e['loc']}: {e['msg']}" for e in errors])
        return StandardResponse.error(code=400, msg=error_msg)

    @api.exception_handler(AuthenticationError)
    def authentication_error_handler(request: HttpRequest, exc: AuthenticationError):
        return StandardResponse.error(code=401, msg=str(exc))

    @api.exception_handler(AuthorizationError)
    def authorization_error_handler(request: HttpRequest, exc: AuthorizationError):
        return StandardResponse.error(code=403, msg=str(exc))

    @api.exception_handler(PermissionDenied)
    def permission_denied_handler(request: HttpRequest, exc: PermissionDenied):
        return StandardResponse.error(code=403, msg='拒绝访问')

    @api.exception_handler(ObjectDoesNotExist)
    def not_found_handler(request: HttpRequest, exc: ObjectDoesNotExist):
        return StandardResponse.error(code=404, msg='资源不存在')

    @api.exception_handler(Exception)
    def general_exception_handler(request: HttpRequest, exc: Exception):
        return StandardResponse.error(code=500, msg='服务器内部错误')
