# 部署手册

## 宝塔面板 Python 项目部署

### 前提条件

1. 宝塔面板已安装
2. Python 项目管理器已安装
3. PostgreSQL 数据库已配置
4. Redis 服务已安装

### 部署步骤

#### 1. 准备工作

1. 在宝塔面板中创建网站
2. 配置 PostgreSQL 数据库并导入初始数据
3. 确保 Redis 服务运行正常

#### 2. 上传代码

通过 Git 或文件管理器上传代码到服务器：
```
/www/wwwroot/project/backend/
```

#### 3. 安装依赖

```bash
cd /www/wwwroot/project/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements/production.txt
```

#### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件配置数据库、Redis 等
```

#### 5. 数据库迁移

```bash
python manage.py migrate
python manage.py createsuperuser
```

#### 6. 配置 Python 项目

在宝塔面板中：
1. 网站 → Python 项目 → 添加项目
2. 填写配置：
   - 项目路径：`/www/wwwroot/project/backend`
   - 启动文件：`config/wsgi.py`
   - 框架：Django
   - 端口：8000
   - 虚拟环境：`/www/wwwroot/project/backend/venv`

#### 7. 配置 Nginx 反代

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /www/wwwroot/project/backend/staticfiles/;
    }
}
```

#### 8. 配置 SSL（可选）

在宝塔面板中为网站申请 SSL 证书

### Docker 部署

#### Dockerfile

项目已提供多阶段构建 Dockerfile：

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements/production.txt .
RUN pip install -r production.txt
COPY backend/ .
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

#### 构建和运行

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

### 前端部署

#### 构建

```bash
cd frontend
npm install
npm run build
```

#### 部署 dist 目录

将 `dist` 目录部署到 Nginx 或 CDN

### 环境变量配置

| 变量名 | 说明 | 示例 |
|--------|------|------|
| DJANGO_SECRET_KEY | Django 密钥 | 生成随机字符串 |
| DJANGO_DEBUG | 调试模式 | False |
| DJANGO_ALLOWED_HOSTS | 允许的域名 | example.com |
| DB_NAME | 数据库名 | template_db |
| DB_USER | 数据库用户 | postgres |
| DB_PASSWORD | 数据库密码 | - |
| DB_HOST | 数据库地址 | localhost |
| DB_PORT | 数据库端口 | 5432 |
| REDIS_HOST | Redis 地址 | localhost |
| REDIS_PORT | Redis 端口 | 6379 |
| JWT_SECRET | JWT 密钥 | 生成随机字符串 |

### 验证部署

1. 访问 `http://your-domain.com/docs/` 查看 Swagger UI
2. 测试注册接口
3. 测试登录接口
4. 检查日志输出
