"""Pagination utilities for Ninja."""
from ninja import Schema
from typing import Generic, TypeVar, List, Optional
from pydantic import Field

T = TypeVar('T')


class LimitOffsetPagination(Schema, Generic[T]):
    """Limit offset pagination response."""
    items: List[T] = Field(default_factory=list, description='数据列表')
    total: int = Field(default=0, description='总数')
    limit: int = Field(default=20, description='每页数量')
    offset: int = Field(default=0, description='偏移量')


def paginate_query(queryset, limit: int = 20, offset: int = 0):
    """Paginate queryset with limit and offset."""
    total = queryset.count()
    items = queryset[offset:offset + limit]
    return {
        'items': items,
        'total': total,
        'limit': limit,
        'offset': offset
    }
