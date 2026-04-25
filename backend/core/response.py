"""Standard response wrapper for Ninja."""
from ninja import Schema
from typing import Generic, TypeVar, Optional
from pydantic import Field
import uuid

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
        return cls(code=200, data=data, msg=msg, request_id=str(uuid.uuid4()))

    @classmethod
    def error(cls, code: int = 400, msg: str = 'error'):
        """错误响应."""
        return cls(code=code, msg=msg, request_id=str(uuid.uuid4()))


def create_response(data: T = None, msg: str = 'ok') -> dict:
    """创建成功响应."""
    return StandardResponse.ok(data=data, msg=msg).dict()


def create_error_response(code: int = 400, msg: str = 'error', data: Optional[T] = None) -> dict:
    """创建错误响应."""
    response = StandardResponse.error(code=code, msg=msg)
    if data is not None:
        response.data = data
    return response.dict()
