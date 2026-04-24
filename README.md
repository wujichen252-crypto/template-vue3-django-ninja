# Template Repository

前后端分离的全栈项目模板，基于 Vue 3 + Django-Ninja 构建。

## 项目结构

```
template-vue3-django-ninja/
├── frontend/          # Vue3 前端
├── backend/           # Django-Ninja 后端
├── docs/              # 项目文档
├── .trae/rules/       # AI 规则文件
└── .github/           # GitHub 配置
```

## 快速开始

### 前端

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173

### 后端

#### 1. 创建虚拟环境

**Linux/Mac:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
```

#### 2. 安装依赖

```bash
pip install -r requirements/local.txt
```

#### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库和 Redis 连接
```

#### 4. 数据库迁移

```bash
python manage.py migrate
```

#### 5. 创建管理员账号

```bash
python manage.py createsuperuser
# 或使用初始化脚本
python manage.py runscript init_superuser
```

#### 6. 启动开发服务器

```bash
python manage.py runserver
```

访问 http://localhost:8000/docs 查看 API 文档

## 技术栈

### 前端
- Vue 3.4 + TypeScript
- Vite 5
- Pinia (状态管理)
- Vue Router 4
- Axios
- Tailwind CSS
- Element Plus

### 后端
- Python 3.11+
- Django 5.0
- Django-Ninja 1.1
- PostgreSQL
- Redis
- PyJWT
- Gunicorn
- Whitenoise

## 环境变量

后端 `.env` 文件配置项：

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| DJANGO_SECRET_KEY | Django 密钥 | - |
| DJANGO_DEBUG | 调试模式 | True |
| DB_NAME | 数据库名 | template_db |
| DB_USER | 数据库用户 | postgres |
| DB_PASSWORD | 数据库密码 | - |
| DB_HOST | 数据库主机 | localhost |
| DB_PORT | 数据库端口 | 5432 |
| REDIS_HOST | Redis 主机 | localhost |
| REDIS_PORT | Redis 端口 | 6379 |
| JWT_SECRET | JWT 密钥 | - |

## 部署

### 开发环境

前端：`npm run dev`
后端：`python manage.py runserver`

### 生产环境

前端：执行 `npm run build`，部署 dist 目录

后端：
```bash
pip install -r requirements/production.txt
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### Docker 部署

#### 后端

```bash
# 构建镜像
docker build -t template-backend:latest .

# 运行容器
docker run -d -p 8000:8000 \
  -e DJANGO_SECRET_KEY=your-secret-key \
  -e DB_NAME=template_db \
  -e DB_USER=postgres \
  -e DB_PASSWORD=your-password \
  -e DB_HOST=host.docker.internal \
  -e REDIS_HOST=host.docker.internal \
  template-backend:latest
```

#### 前端

```bash
cd frontend
npm install
npm run build
```

将 `dist` 目录部署到 Nginx 或 CDN

### 宝塔面板部署

1. 宝塔 → 网站 → Python 项目 → 添加项目
2. 路径：`/www/wwwroot/project/backend`
3. 启动文件：`config/wsgi.py`
4. 框架：`Django`
5. 端口：`8000`（Nginx 反代）

## API 文档

启动后端后访问：
- Swagger UI: http://localhost:8000/docs/
- OpenAPI JSON: http://localhost:8000/openapi.json

## License

MIT
