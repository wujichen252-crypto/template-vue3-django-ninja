# Vue3 + Django-Ninja 全栈模板

基于 Vue 3 + Django-Ninja 的全栈开发模板，包含完整的用户认证、权限管理、缓存、限流等基础设施。

## 技术栈

### 前端
- Vue 3.4 + TypeScript + Vite 5
- Pinia（状态管理）
- Vue Router 4
- Element Plus（UI 组件库）
- Tailwind CSS（样式）
- Axios（HTTP 客户端）
- Vitest（单元测试）

### 后端
- Python 3.11 + Django 5.0
- Django-Ninja 1.1（API 框架）
- PostgreSQL（数据库）
- Redis（缓存）
- PyJWT（认证）
- bcrypt（密码哈希）

## 项目结构

```
.
├── frontend/                 # 前端项目
│   ├── src/
│   │   ├── api/             # API 接口
│   │   ├── components/      # 公共组件
│   │   ├── composables/     # 组合式函数
│   │   ├── router/          # 路由配置
│   │   ├── stores/          # Pinia 状态
│   │   ├── types/           # TypeScript 类型
│   │   ├── utils/           # 工具函数
│   │   └── views/           # 页面组件
│   ├── Dockerfile
│   └── nginx.conf
├── backend/                  # 后端项目
│   ├── apps/                # 业务应用
│   │   └── users/           # 用户模块
│   ├── config/              # Django 配置
│   ├── core/                # 核心基础设施
│   └── requirements/        # 依赖管理
├── docker-compose.yml        # Docker 编排
└── .github/workflows/        # CI/CD
```

## 快速开始

### 方式一：Docker Compose（推荐）

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

服务地址：
- 前端：http://localhost:5173
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs/

### 方式二：本地开发

#### 环境要求
- Python 3.11+
- Node.js 20+
- PostgreSQL 15
- Redis 7

#### 后端启动

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements/local.txt

# 配置环境变量
cp .env.example .env

# 数据库迁移
python manage.py migrate

# 启动服务
python manage.py runserver
```

#### 前端启动

```bash
cd frontend

# 安装依赖
pnpm install

# 启动开发服务器
pnpm run dev
```

## 开发规范

### 前端规范
- 组件使用 `<script setup>` + Composition API
- 组件命名 PascalCase，变量/函数 camelCase
- 使用 Tailwind CSS 工具类，黑白极简主题
- 严格 TypeScript 类型定义，禁止 any

### 后端规范
- RESTful API 风格
- 统一响应格式：`{ "code": 200, "data": {}, "msg": "ok" }`
- 分层架构：api.py → services.py → models.py
- 函数长度不超过 50 行，必须写 docstring

## 可用 API

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/v1/auth/register | POST | 用户注册 |
| /api/v1/auth/login | POST | 用户登录 |
| /api/v1/auth/refresh | POST | 刷新 Token |
| /api/v1/users/me | GET | 获取当前用户 |

## 测试

### 前端测试
```bash
cd frontend
pnpm run test
```

### 后端测试
```bash
cd backend
pytest
```

## 部署

### 生产环境构建

```bash
# 前端构建
cd frontend
pnpm run build

# 后端收集静态文件
cd backend
python manage.py collectstatic
```

### Docker 生产部署

```bash
# 构建生产镜像
docker-compose -f docker-compose.prod.yml up -d
```

## 环境变量

### 后端 (.env)

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| DJANGO_SECRET_KEY | Django 密钥 | - |
| DJANGO_DEBUG | 调试模式 | True |
| DB_NAME | 数据库名 | template_db |
| DB_USER | 数据库用户 | postgres |
| DB_PASSWORD | 数据库密码 | - |
| REDIS_HOST | Redis 地址 | localhost |
| JWT_SECRET | JWT 密钥 | - |

### 前端 (.env)

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| VITE_APP_TITLE | 应用标题 | Template Vue3 App |
| VITE_API_BASE_URL | API 基础路径 | /api/v1 |

## 许可证

MIT
