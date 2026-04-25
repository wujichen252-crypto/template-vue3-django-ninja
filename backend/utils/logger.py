"""Logger utilities - 统一使用 Django LOGGING 配置."""
import logging
from typing import Optional


def get_logger(name: str, request_id: Optional[str] = None) -> logging.Logger:
    """
    获取 Django 配置的 logger，支持 request_id 注入.
    
    Args:
        name: logger 名称，通常使用 __name__
        request_id: 请求 ID（可选）
    
    Returns:
        配置好的 Logger 实例
    """
    logger = logging.getLogger(name)
    
    # 如果有 request_id，可以通过 extra 参数传递
    if request_id:
        # 使用 LoggerAdapter 自动注入 request_id
        return logging.LoggerAdapter(logger, {'request_id': request_id})
    
    return logger


def log_request(
    logger: logging.Logger,
    method: str,
    path: str,
    status_code: int,
    duration: float,
    request_id: Optional[str] = None
):
    """
    记录请求日志.
    
    Args:
        logger: Logger 实例
        method: HTTP 方法
        path: 请求路径
        status_code: 响应状态码
        duration: 请求耗时（秒）
        request_id: 请求 ID
    """
    extra = {'request_id': request_id} if request_id else {}
    logger.info(
        f"{method} {path} - {status_code} - {duration:.3f}s",
        extra=extra
    )


def log_slow_query(
    logger: logging.Logger,
    query: str,
    duration: float,
    request_id: Optional[str] = None
):
    """
    记录慢查询日志.
    
    Args:
        logger: Logger 实例
        query: SQL 查询语句
        duration: 查询耗时（秒）
        request_id: 请求 ID
    """
    extra = {'request_id': request_id} if request_id else {}
    logger.warning(
        f"慢查询: {duration:.3f}s - {query[:200]}",
        extra=extra
    )
