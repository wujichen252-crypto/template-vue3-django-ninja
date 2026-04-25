"""Gunicorn 生产环境配置

性能优化配置，根据 CPU 核心数动态调整 worker 数量
公式：workers = 2 * CPU核心数 + 1
"""
import multiprocessing
import os

# 服务器绑定
bind = f"0.0.0.0:{os.getenv('GUNICORN_PORT', '8000')}"

# Worker 配置
workers = int(os.getenv('GUNICORN_WORKERS', '0')) or (2 * multiprocessing.cpu_count() + 1)
worker_class = 'gthread'
threads = int(os.getenv('GUNICORN_THREADS', '2'))

# Worker 生命周期
worker_connections = 1000
timeout = int(os.getenv('GUNICORN_TIMEOUT', '30'))
keepalive = int(os.getenv('GUNICORN_KEEPALIVE', '5'))

# 优雅重启超时
graceful_timeout = 30

# 请求限制
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# 日志配置
accesslog = os.getenv('GUNICORN_ACCESS_LOG', '-')
errorlog = os.getenv('GUNICORN_ERROR_LOG', '-')
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')

# 性能优化
preload_app = True
max_requests = 1000
max_requests_jitter = 50

# 进程管理
pidfile = os.getenv('GUNICORN_PIDFILE', '/tmp/gunicorn.pid')

# Worker 临时目录
worker_tmp_dir = '/dev/shm'
