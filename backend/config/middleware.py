"""Custom middleware."""
import uuid
import time
import logging
from django.http import HttpRequest, HttpResponse
from django.conf import settings
from django.db import connection, reset_queries

logger = logging.getLogger(__name__)


class RequestIDMiddleware:
    """Middleware to generate or propagate request_id for logging."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        request.request_id = request_id

        response = self.get_response(request)
        response['X-Request-ID'] = request_id
        return response


class QueryPerformanceMiddleware:
    """数据库查询性能监控中间件

    功能:
    - 记录慢查询（超过阈值）
    - 记录 N+1 查询问题（单次请求查询过多）
    - 仅在 DEBUG 模式或生产环境配置下启用
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.slow_query_threshold = getattr(settings, 'SLOW_QUERY_THRESHOLD', 1.0)
        self.max_queries_per_request = getattr(settings, 'MAX_QUERIES_PER_REQUEST', 50)

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # 跳过静态文件和 admin
        if request.path.startswith(('/static/', '/media/', '/admin/')):
            return self.get_response(request)

        # 启用查询记录
        if settings.DEBUG:
            settings.DEBUG_QUERIES = True
            reset_queries()

        start_time = time.time()
        query_count_before = len(connection.queries) if settings.DEBUG else 0

        response = self.get_response(request)

        duration = time.time() - start_time
        query_count_after = len(connection.queries) if settings.DEBUG else 0

        # 记录慢请求
        if duration > self.slow_query_threshold:
            request_id = getattr(request, 'request_id', 'unknown')
            logger.warning(
                f"慢请求: {request.method} {request.path} "
                f"耗时: {duration:.3f}s "
                f"查询数: {query_count_after - query_count_before} "
                f"request_id: {request_id}"
            )

        # 记录 N+1 查询问题
        if settings.DEBUG and (query_count_after - query_count_before) > self.max_queries_per_request:
            request_id = getattr(request, 'request_id', 'unknown')
            logger.warning(
                f"N+1 查询警告: {request.method} {request.path} "
                f"查询数: {query_count_after - query_count_before} "
                f"(阈值: {self.max_queries_per_request}) "
                f"request_id: {request_id}"
            )

            # 在 DEBUG 模式下，打印最慢的查询
            if connection.queries:
                slow_queries = sorted(
                    connection.queries,
                    key=lambda q: float(q.get('time', 0)),
                    reverse=True
                )[:5]

                for query in slow_queries:
                    logger.debug(
                        f"慢查询 SQL: {query.get('sql', '')[:200]} "
                        f"耗时: {query.get('time', 0)}s"
                    )

        # 添加性能响应头（仅 DEBUG 模式）
        if settings.DEBUG:
            response['X-Query-Count'] = str(query_count_after - query_count_before)
            response['X-Response-Time'] = f"{duration:.3f}s"

        return response
