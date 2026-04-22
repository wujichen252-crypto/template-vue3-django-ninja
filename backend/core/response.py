"""Standard response wrapper for Ninja."""
from ninja import Schema
from typing import Generic, TypeVar, Optional
from pydantic import Field

T = TypeVar('T')


class StandardResponse(Schema, Generic[T]):
    """统一响应封装格式."""
    code: int = Field(default=200, description='状态码')
    data: Optional[T] = Field(default=None, description='响应数据')
    msg: str = Field(default='ok', description='消息')
    request_id: str = Field(default='', description='请求ID')

    @classmethod
    def ok(cls, data: T = None, msg: str = 'ok'):
        """成功响应."""
        return cls(code=200, data=data, msg=msg)

    @classmethod
    def error(cls, code: int = 400, msg: str = 'error'):
        """错误响应."""
        return cls(code=code, msg=msg)
