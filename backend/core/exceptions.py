"""Core exceptions module."""
import logging

logger = logging.getLogger(__name__)


class AuthenticationError(ValueError):
    """认证失败异常."""
    pass


class AuthorizationError(ValueError):
    """授权失败异常."""
    pass


"""Global exception handlers for Ninja API."""
from ninja import NinjaAPI
from ninja.errors import HttpError
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpRequest, JsonResponse
from pydantic import ValidationError as PydanticValidationError
from core.response import StandardResponse
from core.exceptions import AuthenticationError, AuthorizationError
from core.ratelimit import add_rate_limit_headers


def register_exception_handlers(api: NinjaAPI):
    """Register global exception handlers."""

    @api.exception_handler(ValidationError)
    def validation_error_handler(request: HttpRequest, exc: ValidationError):
        logger.warning(f"数据验证失败: {exc}")
        return StandardResponse.error(code=400, msg='数据验证失败')

    @api.exception_handler(PydanticValidationError)
    def pydantic_validation_error_handler(request: HttpRequest, exc: PydanticValidationError):
        errors = exc.errors()
        error_msg = '; '.join([f"{e['loc']}: {e['msg']}" for e in errors])
        logger.warning(f"Pydantic 验证失败: {error_msg}")
        return StandardResponse.error(code=400, msg=error_msg)

    @api.exception_handler(AuthenticationError)
    def authentication_error_handler(request: HttpRequest, exc: AuthenticationError):
        logger.warning(f"认证失败: {exc}")
        return StandardResponse.error(code=401, msg=str(exc))

    @api.exception_handler(AuthorizationError)
    def authorization_error_handler(request: HttpRequest, exc: AuthorizationError):
        logger.warning(f"授权失败: {exc}")
        return StandardResponse.error(code=403, msg=str(exc))

    @api.exception_handler(PermissionDenied)
    def permission_denied_handler(request: HttpRequest, exc: PermissionDenied):
        logger.warning(f"权限拒绝: {request.path}")
        return StandardResponse.error(code=403, msg='拒绝访问')

    @api.exception_handler(ObjectDoesNotExist)
    def not_found_handler(request: HttpRequest, exc: ObjectDoesNotExist):
        logger.warning(f"资源不存在: {request.path}")
        return StandardResponse.error(code=404, msg='资源不存在')

    @api.exception_handler(HttpError)
    def http_error_handler(request: HttpRequest, exc: HttpError):
        """处理 HTTP 错误（包括限流 429）"""
        response = StandardResponse.error(code=exc.status_code, msg=str(exc))

        # 如果是限流错误，添加限流响应头
        if exc.status_code == 429:
            rate_limit_info = getattr(request, '_rate_limit_info', None)
            if rate_limit_info:
                response = add_rate_limit_headers(response, rate_limit_info)

        return response

    @api.exception_handler(Exception)
    def general_exception_handler(request: HttpRequest, exc: Exception):
        """通用异常处理器 - 记录详细堆栈信息"""
        request_id = getattr(request, 'request_id', 'unknown')
        logger.error(
            f"服务器内部错误: {request.method} {request.path}\n"
            f"request_id: {request_id}\n"
            f"异常类型: {type(exc).__name__}\n"
            f"异常信息: {str(exc)}",
            exc_info=True  # 包含完整堆栈跟踪
        )
        return StandardResponse.error(code=500, msg='服务器内部错误')
