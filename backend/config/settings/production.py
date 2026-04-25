"""Production settings."""
import os
from .base import *

DEBUG = False

ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',')

# 安全设置
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# WhiteNoise 静态文件处理
MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
] + MIDDLEWARE

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# 生产环境数据库连接池优化
DATABASES['default']['CONN_MAX_AGE'] = int(os.getenv('DB_CONN_MAX_AGE', '900'))  # 15分钟
DATABASES['default']['OPTIONS'].update({
    'MAX_CONNS': int(os.getenv('DB_MAX_CONNS', '20')),
    'MIN_CONNS': int(os.getenv('DB_MIN_CONNS', '5')),
})

# 缓存优化 - 生产环境更长的过期时间
CACHES['default']['OPTIONS']['SOCKET_CONNECT_TIMEOUT'] = 5
CACHES['default']['OPTIONS']['SOCKET_TIMEOUT'] = 5
CACHES['default']['OPTIONS']['CONNECTION_POOL_KWARGS'] = {
    'max_connections': 50,
    'retry_on_timeout': True,
}

# 性能监控
SLOW_QUERY_THRESHOLD = float(os.getenv('SLOW_QUERY_THRESHOLD', '1.0'))
MAX_QUERIES_PER_REQUEST = int(os.getenv('MAX_QUERIES_PER_REQUEST', '50'))

LOGGING['loggers']['django']['level'] = 'INFO'
