# 后端 Django-Ninja 规则文件

## 技术栈
- Python 3.11+
- Django 5.0
- Django-Ninja 1.1
- PostgreSQL
- Redis
- PyJWT
- Pydantic

## 项目结构

```
backend/
├── config/           # Django 项目配置
│   ├── settings/     # 设置分层 (base/local/production)
│   ├── urls.py       # 路由配置
│   └── middleware.py # 中间件
├── apps/             # 业务应用
│   └── users/        # 用户模块
│       ├── models.py # 数据模型
│       ├── schemas.py # Ninja Schema
│       ├── api.py    # API 路由
│       ├── services.py # 业务逻辑
│       └── admin.py  # Django Admin
├── core/             # 核心基础设施
│   ├── auth.py       # JWT 认证
│   ├── response.py   # 统一响应
│   ├── exceptions.py # 异常处理
│   └── pagination.py # 分页
└── utils/           # 工具模块
    └── logger.py     # 日志配置
```

## 代码规范

### 命名规范
- 类名：PascalCase
- 函数/变量：snake_case
- 常量：UPPER_SNAKE_CASE
- 包名：snake_case

### API 设计
- RESTful 风格
- 统一响应格式：{ "code": 200, "data": {}, "msg": "ok" }
- 使用 Ninja Router 组织路由

### 分层架构
- Handler (api.py): 接收请求，参数校验
- Service (services.py): 业务逻辑
- Model (models.py): 数据模型

### 认证
- 使用 PyJWT 自研 JWT 认证
- Access Token：2小时有效期
- Refresh Token：7天有效期
- 密码必须 bcrypt 哈希存储

### 异常处理
- 使用 Ninja 的 @api.exception_handler
- ValidationError → 400
- AuthenticationError → 401
- PermissionError → 403
- ObjectDoesNotExist → 404
- 其他异常 → 500

### 配置分层
- base.py: 通用配置
- local.py: 开发环境 (DEBUG=True)
- production.py: 生产环境 (DEBUG=False, whitenoise)
