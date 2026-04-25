"""Pagination utilities for Ninja."""
from ninja import Schema
from typing import Generic, TypeVar, List, Optional
from pydantic import Field
from django.db.models import QuerySet

T = TypeVar('T')


class LimitOffsetPagination(Schema, Generic[T]):
    """Limit offset pagination response."""
    items: List[T] = Field(default_factory=list, description='数据列表')
    total: int = Field(default=0, description='总数')
    limit: int = Field(default=20, description='每页数量')
    offset: int = Field(default=0, description='偏移量')


class CursorPagination(Schema, Generic[T]):
    """Cursor pagination response (高性能，适合大数据量)."""
    items: List[T] = Field(default_factory=list, description='数据列表')
    next_cursor: Optional[str] = Field(None, description='下一页游标')
    has_next: bool = Field(default=False, description='是否有下一页')
    limit: int = Field(default=20, description='每页数量')


def paginate_limit_offset(queryset: QuerySet, limit: int = 20, offset: int = 0) -> dict:
    """Paginate queryset with limit and offset."""
    total = queryset.count()
    items = list(queryset[offset:offset + limit])
    return {
        'items': items,
        'total': total,
        'limit': limit,
        'offset': offset
    }


def paginate_cursor(
    queryset: QuerySet,
    cursor: Optional[str] = None,
    limit: int = 20,
    cursor_field: str = 'id'
) -> dict:
    """
    Cursor-based pagination (高性能，适合大数据量).
    
    Args:
        queryset: Django QuerySet
        cursor: 上一页返回的游标（通常是最后一条记录的 ID）
        limit: 每页数量
        cursor_field: 游标字段名，默认 'id'
    """
    # 如果有游标，查询大于游标值的记录
    if cursor:
        queryset = queryset.filter(**{f'{cursor_field}__gt': cursor})
    
    # 按游标字段排序
    queryset = queryset.order_by(cursor_field)
    
    # 多取一条判断是否有下一页
    items = list(queryset[:limit + 1])
    has_next = len(items) > limit
    
    if has_next:
        # 移除多余的一条
        items = items[:limit]
        # 返回最后一条记录的游标值
        next_cursor = str(getattr(items[-1], cursor_field))
    else:
        next_cursor = None
    
    return {
        'items': items,
        'next_cursor': next_cursor,
        'has_next': has_next,
        'limit': limit
    }
