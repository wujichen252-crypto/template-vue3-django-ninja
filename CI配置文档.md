# 可配置模板仓库 CI/CD 设计指南（Django-Ninja 后端适配版）

> **文档编号**：TECH-DEV-004  
> **归档日期**：2026-04-23  
> **关联项目**：NeuraMind 智脑笔记系统（Vue3 + Django-Ninja 全栈模板）  
> **文档类型**：工程化实践与模板设计规范

---

## 目录

1. [与 Go 后端版本的核心差异](#一与-go-后端版本的核心差异)
2. [设计目标与核心原则](#二设计目标与核心原则)
3. [模板仓库目录结构](#三模板仓库目录结构)
4. [可配置 CI 架构设计](#四可配置-ci-架构设计)
5. [配置文件详解](#五配置文件详解)
6. [Django-Ninja 后端部署清单](#六django-ninja-后端部署清单)
7. [初始化与配置流程](#七初始化与配置流程)
8. [多环境支持方案](#八多环境支持方案)
9. [安全与权限设计](#九安全与权限设计)
10. [使用手册（给模板使用者）](#十使用手册给模板使用者)
11. [完整文件参考](#十一完整文件参考)

---

## 一、与 Go 后端版本的核心差异

| 维度           | Gin (Go) 版本                | Django-Ninja (Python) 版本                    |
| -------------- | ---------------------------- | --------------------------------------------- |
| **构建产物**   | 静态二进制文件（`go build`） | 源码 + 依赖（解释型，需服务器有 Python 环境） |
| **部署方式**   | CI 编译后 SCP 上传二进制     | CI 上传源码，**服务器端执行** `pip install`   |
| **数据库操作** | 无（由开发者手动管理）       | **必须**支持 `migrate` 自动迁移               |
| **静态文件**   | 前端 `dist/` 即可            | 可能需要 `collectstatic`（Admin、API Docs）   |
| **进程管理**   | 直接运行二进制               | 需 Gunicorn/Uvicorn + systemd/Supervisor      |
| **环境隔离**   | 单文件 + 环境变量            | 强烈建议 `venv` 虚拟环境                      |

**结论**：Django-Ninja 的 CI 部署重心从"编译上传"转向了**"服务器端环境配置与热更新"**。

---

## 二、设计目标与核心原则

与通用模板一致，但增加 Python 生态的特有约束：

1. **零硬编码**：YAML 中不出现 IP、路径、域名、Python 版本等具体值
2. **服务器端自治**：CI 只负责"传送代码"，安装依赖、迁移、重启在服务器上完成
3. **虚拟环境感知**：支持通过变量指定服务器上的 `venv` 路径
4. **防御性编程**：未配置完成时，CI 优雅跳过；数据库操作可开关
5. **宝塔兼容**：提供 systemd 和宝塔 Python 项目管理器两套方案

---

## 三、模板仓库目录结构

```
neuramind-template/                 ← 模板仓库根目录
├── .github/
│   └── workflows/
│       ├── ci-check.yml            ← 代码质量检查（无部署，开箱即用）
│       └── deploy.yml              ← 可配置部署流水线（未配置时自动跳过）
├── scripts/
│   └── setup-ci.sh               ← 本地初始化脚本
├── frontend/                       ← Vue3 前端（目录名可配置）
├── backend/                        ← Django-Ninja 后端（目录名可配置）
│   ├── manage.py
│   ├── requirements.txt            ← 或 pyproject.toml
│   └── neuramind/
│       ├── settings.py
│       └── urls.py
├── .env.example                    ← 环境变量模板（含 Django SECRET_KEY 等）
├── README.md
└── LICENSE
```

---

## 四、可配置 CI 架构设计

### 4.1 配置分层模型

```
┌─────────────────────────────────────────────┐
│  层 1：代码层（YAML 文件）                     │
│  └── 只定义流程逻辑，不出现任何具体值             │
│       │                                       │
│  层 2：仓库变量层（Settings → Variables）      │
│  └── 非敏感配置：IP、路径、Python版本、迁移开关    │
│       │                                       │
│  层 3：仓库密钥层（Settings → Secrets）        │
│  └── 敏感信息：SSH私钥、Django SECRET_KEY、DB密码 │
└─────────────────────────────────────────────┘
```

### 4.2 Django-Ninja 特有命名规范

| 类型               | 前缀                  | 示例                  | 存放位置  |
| ------------------ | --------------------- | --------------------- | --------- |
| 部署服务器相关     | `DEPLOY_`             | `DEPLOY_SERVER_HOST`  | Variables |
| 项目路径相关       | `PROJECT_`            | `PROJECT_BACKEND_DIR` | Variables |
| Python/Django 配置 | `DJANGO_` / `PYTHON_` | `PYTHON_VERSION`      | Variables |
| 运行时开关         | `ENABLE_`             | `ENABLE_MIGRATE`      | Variables |
| 敏感凭据           | `SSH_` / `SECRET_`    | `SSH_PRIVATE_KEY`     | Secrets   |

---

## 五、配置文件详解

### 5.1 代码质量检查（ci-check.yml）

**特点**：无需任何配置，从模板创建后立即生效。

```yaml
name: CI Check

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  FRONTEND_DIR: ${{ vars.PROJECT_FRONTEND_DIR || './frontend' }}
  BACKEND_DIR: ${{ vars.PROJECT_BACKEND_DIR || './backend' }}
  PYTHON_VER: ${{ vars.PYTHON_VERSION || '3.11' }}
  NODE_VER: ${{ vars.NODE_VERSION || '20' }}
  REQUIREMENTS: ${{ vars.PROJECT_REQUIREMENTS_FILE || 'requirements.txt' }}

jobs:
  frontend-check:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ${{ env.FRONTEND_DIR }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VER }}
          cache: 'npm'
          cache-dependency-path: '${{ env.FRONTEND_DIR }}/package-lock.json'
      - run: npm ci
      - run: npm run lint
      - run: npm run build

  backend-check:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ${{ env.BACKEND_DIR }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VER }}
          cache: 'pip'
          cache-dependency-path: '${{ env.BACKEND_DIR }}/${{ env.REQUIREMENTS }}'
      
      - name: Install dependencies
        run: pip install -r ${{ env.REQUIREMENTS }}
      
      - name: Django System Check
        run: python manage.py check --deploy
        env:
          DJANGO_SETTINGS_MODULE: ${{ vars.DJANGO_SETTINGS_MODULE || 'neuramind.settings' }}
          # 提供一个虚拟 SECRET_KEY 用于 CI 检查
          SECRET_KEY: ci-check-key-not-for-production
      
      - name: Run Tests
        run: python manage.py test
        env:
          DJANGO_SETTINGS_MODULE: ${{ vars.DJANGO_SETTINGS_MODULE || 'neuramind.settings' }}
          SECRET_KEY: ci-check-key-not-for-production
```

**设计要点**：

- `actions/setup-python@v5` 自动处理 Python 环境
- `cache: 'pip'` 缓存依赖，大幅加速后续构建
- Django `check --deploy` 会检查生产环境配置问题（如 `DEBUG=True` 等）
- 使用虚拟 `SECRET_KEY` 避免 CI 阶段依赖 Secrets

---

### 5.2 可配置部署流水线（deploy.yml）

**特点**：未配置完成时，部署 Job 自动跳过，不会报错。

```yaml
name: Deploy

on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      environment:
        description: '部署环境'
        required: true
        default: 'production'
        type: choice
        options:
          - production
          - staging

env:
  FRONTEND_DIR: ${{ vars.PROJECT_FRONTEND_DIR || './frontend' }}
  BACKEND_DIR: ${{ vars.PROJECT_BACKEND_DIR || './backend' }}
  NODE_VER: ${{ vars.NODE_VERSION || '20' }}
  REQUIREMENTS: ${{ vars.PROJECT_REQUIREMENTS_FILE || 'requirements.txt' }}

jobs:
  # ==========================================
  # Job 1: 构建前端
  # ==========================================
  build-frontend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ${{ env.FRONTEND_DIR }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VER }}
          cache: 'npm'
          cache-dependency-path: '${{ env.FRONTEND_DIR }}/package-lock.json'
      - run: npm ci
      - run: npm run build
      - uses: actions/upload-artifact@v4
        with:
          name: frontend-dist
          path: ${{ env.FRONTEND_DIR }}/dist
          retention-days: 3

  # ==========================================
  # Job 2: 后端检查与打包
  # ==========================================
  package-backend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ${{ env.BACKEND_DIR }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ vars.PYTHON_VERSION || '3.11' }}
          cache: 'pip'
          cache-dependency-path: '${{ env.BACKEND_DIR }}/${{ env.REQUIREMENTS }}'
      
      - run: pip install -r ${{ env.REQUIREMENTS }}
      - run: python manage.py test
        env:
          DJANGO_SETTINGS_MODULE: ${{ vars.DJANGO_SETTINGS_MODULE || 'neuramind.settings' }}
          SECRET_KEY: ci-test-key
      
      # 将后端代码打包为 tarball，方便一次性上传
      - name: Package backend
        run: |
          cd ..
          tar -czf backend.tar.gz \
            --exclude='__pycache__' \
            --exclude='*.pyc' \
            --exclude='.git' \
            --exclude='venv' \
            ${{ env.BACKEND_DIR }}
      
      - uses: actions/upload-artifact@v4
        with:
          name: backend-source
          path: backend.tar.gz
          retention-days: 3

  # ==========================================
  # Job 3: 部署（带前置条件检查）
  # ==========================================
  deploy:
    needs: [build-frontend, package-backend]
    runs-on: ubuntu-latest
    
    # 防御性条件：关键变量未配置时直接跳过
    if: |
      vars.DEPLOY_SERVER_HOST != '' &&
      vars.DEPLOY_FRONTEND_PATH != '' &&
      vars.DEPLOY_BACKEND_PATH != '' &&
      secrets.SSH_PRIVATE_KEY != ''
    
    steps:
      # 下载前端产物
      - name: Download frontend artifact
        uses: actions/download-artifact@v4
        with:
          name: frontend-dist
          path: ./dist
      
      # 下载后端源码包
      - name: Download backend artifact
        uses: actions/download-artifact@v4
        with:
          name: backend-source
          path: ./

      # 部署前端静态文件
      - name: Deploy Frontend
        uses: appleboy/scp-action@v0.1.7
        with:
          host: ${{ vars.DEPLOY_SERVER_HOST }}
          username: ${{ vars.DEPLOY_SERVER_USER || 'root' }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          port: ${{ vars.DEPLOY_SERVER_PORT || '22' }}
          source: "dist/*"
          target: ${{ vars.DEPLOY_FRONTEND_PATH }}
          strip_components: 1

      # 部署后端源码包
      - name: Deploy Backend Tarball
        uses: appleboy/scp-action@v0.1.7
        with:
          host: ${{ vars.DEPLOY_SERVER_HOST }}
          username: ${{ vars.DEPLOY_SERVER_USER || 'root' }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          port: ${{ vars.DEPLOY_SERVER_PORT || '22' }}
          source: "backend.tar.gz"
          target: /tmp/

      # 服务器端解压、安装、迁移、重启
      - name: Execute Backend Deployment
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ vars.DEPLOY_SERVER_HOST }}
          username: ${{ vars.DEPLOY_SERVER_USER || 'root' }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          port: ${{ vars.DEPLOY_SERVER_PORT || '22' }}
          script: |
            set -e
            
            BACKEND_PATH="${{ vars.DEPLOY_BACKEND_PATH }}"
            VENV_PATH="${{ vars.DEPLOY_VENV_PATH }}"
            REQUIREMENTS_FILE="${{ vars.PROJECT_REQUIREMENTS_FILE || 'requirements.txt' }}"
            SETTINGS_MODULE="${{ vars.DJANGO_SETTINGS_MODULE || 'neuramind.settings' }}"
            ENABLE_MIGRATE="${{ vars.ENABLE_MIGRATE || 'true' }}"
            ENABLE_COLLECTSTATIC="${{ vars.ENABLE_COLLECTSTATIC || 'false' }}"
            RESTART_CMD="${{ vars.DEPLOY_RESTART_COMMAND || 'sudo systemctl restart neuramind' }}"
            
            echo "===== 开始部署后端 ====="
            
            # 进入后端目录（如果不存在则创建）
            mkdir -p "$BACKEND_PATH"
            cd "$BACKEND_PATH"
            
            # 备份当前版本（以防回滚）
            if [ -d "neuramind" ] || [ -f "manage.py" ]; then
              BACKUP_NAME="backup_$(date +%Y%m%d_%H%M%S)"
              tar -czf "/tmp/$BACKUP_NAME.tar.gz" --exclude='venv' --exclude='__pycache__' . || true
              echo "已备份: /tmp/$BACKUP_NAME.tar.gz"
            fi
            
            # 解压新代码（tarball 包含 backend/ 目录，需要处理层级）
            tar -xzf /tmp/backend.tar.gz -C /tmp/
            
            # 将 /tmp/backend/ 下的内容同步到目标路径（保留 venv）
            rsync -a --delete \
              --exclude='venv' \
              --exclude='.env' \
              --exclude='__pycache__' \
              --exclude='*.pyc' \
              --exclude='db.sqlite3' \
              /tmp/${{ env.BACKEND_DIR }}/ ./ || true
            
            # 激活虚拟环境（如果配置了）
            if [ -n "$VENV_PATH" ] && [ -f "$VENV_PATH/bin/activate" ]; then
              source "$VENV_PATH/bin/activate"
              echo "已激活虚拟环境: $VENV_PATH"
            else
              echo "未配置虚拟环境，使用系统 Python"
            fi
            
            # 安装/更新依赖
            pip install -r "$REQUIREMENTS_FILE" --quiet
            
            # 设置环境变量（从 Secrets 读取的 SECRET_KEY 等由 systemd 管理，这里仅用于 migrate）
            export DJANGO_SETTINGS_MODULE="$SETTINGS_MODULE"
            
            # 数据库迁移（默认开启，可通过变量关闭）
            if [ "$ENABLE_MIGRATE" == "true" ]; then
              echo "执行数据库迁移..."
              python manage.py migrate --noinput
            else
              echo "跳过数据库迁移"
            fi
            
            # 收集静态文件（可选，主要给 Django Admin 和 API Docs 用）
            if [ "$ENABLE_COLLECTSTATIC" == "true" ]; then
              echo "收集静态文件..."
              python manage.py collectstatic --noinput
            fi
            
            # 执行重启命令
            echo "重启服务..."
            eval "$RESTART_CMD"
            
            # 简单健康检查（如果配置了端口）
            if [ -n "${{ vars.APP_PORT }}" ]; then
              sleep 3
              if curl -sf http://127.0.0.1:${{ vars.APP_PORT }}/api/health || curl -sf http://127.0.0.1:${{ vars.APP_PORT }}/admin > /dev/null 2>&1; then
                echo "健康检查通过"
              else
                echo "警告：服务可能未正常启动，请手动检查"
              fi
            fi
            
            echo "===== 后端部署完成 ====="

      # 可选：部署通知
      - name: Notify
        if: vars.DEPLOY_NOTIFY_WEBHOOK != ''
        run: |
          curl -X POST ${{ vars.DEPLOY_NOTIFY_WEBHOOK }} \
            -H 'Content-Type: application/json' \
            -d '{"msg":"[Django-Ninja] 部署成功: ${{ github.repository }}@${{ github.sha }}"}' || true
```

---

## 六、Django-Ninja 后端部署清单

从模板创建新仓库后，在 **Settings → Secrets and variables → Actions** 中配置：

### Secrets（加密）

| 名称              | 必填 | 获取方式                                 |
| ----------------- | ---- | ---------------------------------------- |
| `SSH_PRIVATE_KEY` | ✅    | 服务器执行 `cat ~/.ssh/id_rsa`，粘贴全文 |

### Variables（明文）

| 名称                        | 必填 | 示例                               | 说明                                |
| --------------------------- | ---- | ---------------------------------- | ----------------------------------- |
| `DEPLOY_SERVER_HOST`        | ✅    | `123.456.78.90`                    | 服务器公网 IP                       |
| `DEPLOY_SERVER_USER`        | ❌    | `root`                             | SSH 用户名，默认 root               |
| `DEPLOY_SERVER_PORT`        | ❌    | `22`                               | SSH 端口，默认 22                   |
| `DEPLOY_FRONTEND_PATH`      | ✅    | `/www/wwwroot/neuramind`           | 前端部署目录                        |
| `DEPLOY_BACKEND_PATH`       | ✅    | `/www/neuramind`                   | 后端源码存放目录                    |
| `DEPLOY_VENV_PATH`          | ❌    | `/www/neuramind/venv`              | Python 虚拟环境路径（强烈建议配置） |
| `DEPLOY_RESTART_COMMAND`    | ❌    | `sudo systemctl restart neuramind` | 服务重启命令                        |
| `PROJECT_FRONTEND_DIR`      | ❌    | `./frontend`                       | 前端代码相对路径                    |
| `PROJECT_BACKEND_DIR`       | ❌    | `./backend`                        | 后端代码相对路径                    |
| `PROJECT_REQUIREMENTS_FILE` | ❌    | `requirements.txt`                 | 依赖文件名                          |
| `PYTHON_VERSION`            | ❌    | `3.11`                             | CI 构建用 Python 版本               |
| `NODE_VERSION`              | ❌    | `20`                               | CI 构建用 Node.js 版本              |
| `DJANGO_SETTINGS_MODULE`    | ❌    | `neuramind.settings_production`    | Django 配置模块                     |
| `ENABLE_MIGRATE`            | ❌    | `true`                             | 是否自动执行数据库迁移              |
| `ENABLE_COLLECTSTATIC`      | ❌    | `false`                            | 是否执行 collectstatic              |
| `APP_PORT`                  | ❌    | `8000`                             | 后端服务端口（用于健康检查）        |
| `DEPLOY_NOTIFY_WEBHOOK`     | ❌    | `https://oapi.dingtalk.com/...`    | 可选，部署成功通知地址              |

---

## 七、初始化与配置流程

### 7.1 服务器端准备（比 Go 版本多 Python 环境步骤）

```bash
# 1. 确保服务器有 Python 3.11+（宝塔通常自带，也可手动安装）
python3 --version

# 2. 创建项目目录
mkdir -p /www/neuramind
cd /www/neuramind

# 3. 创建虚拟环境（强烈推荐，避免污染系统 Python）
python3 -m venv venv

# 4. 激活虚拟环境并预装依赖（首次手动，后续由 CI 自动维护）
source venv/bin/activate
pip install -r requirements.txt  # 先把依赖文件传上来，或手动创建

# 5. 生成 SSH 密钥对（用于 GitHub Actions 连接）
ssh-keygen -t rsa -b 4096 -C "github-actions" -f ~/.ssh/github_actions
cat ~/.ssh/github_actions.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# 6. 把私钥填到 GitHub Secrets：SSH_PRIVATE_KEY
cat ~/.ssh/github_actions
```

### 7.2 配置 systemd 服务（Gunicorn 方案）

在服务器创建 `/etc/systemd/system/neuramind.service`：

```ini
[Unit]
Description=NeuraMind Django-Ninja API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/www/neuramind
# 使用虚拟环境的 Gunicorn，绑定 127.0.0.1:8000
ExecStart=/www/neuramind/venv/bin/gunicorn neuramind.asgi:application -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000 -w 4
Restart=always
RestartSec=5
# 环境变量（生产环境密钥、数据库地址等）
Environment="DJANGO_SETTINGS_MODULE=neuramind.settings_production"
Environment="SECRET_KEY=你的生产环境密钥"
Environment="DATABASE_URL=mysql://user:pass@127.0.0.1:3306/neuramind"

[Install]
WantedBy=multi-user.target
```

然后启用：

```bash
sudo systemctl daemon-reload
sudo systemctl enable neuramind
sudo systemctl start neuramind
```

### 7.3 宝塔面板 Nginx 配置（反向代理到 Gunicorn）

宝塔 → 网站 → 你的站点 → 设置 → 配置文件：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # 前端静态文件
    location / {
        root /www/wwwroot/neuramind;
        try_files $uri $uri/ /index.html;
    }
    
    # Django-Ninja API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Django Admin 静态文件（如果开启了 collectstatic）
    location /static/ {
        alias /www/neuramind/static/;
    }
    
    # Django-Ninja API Docs（Swagger UI）
    location /api/docs {
        proxy_pass http://127.0.0.1:8000/api/docs;
        proxy_set_header Host $host;
    }
}
```

---

## 八、多环境支持方案

与通用模板一致，通过 **分支策略** 实现：

```yaml
on:
  push:
    branches:
      - main      # 自动部署到生产
      - develop   # 自动部署到测试
```

在 deploy Job 中根据分支选择不同的 `DJANGO_SETTINGS_MODULE`：

```bash
if [ "${{ github.ref_name }}" == "main" ]; then
  export DJANGO_SETTINGS_MODULE=neuramind.settings_production
else
  export DJANGO_SETTINGS_MODULE=neuramind.settings_staging
fi
```

**建议**：为不同环境准备不同的 `settings.py`：

- `settings_development.py`：`DEBUG=True`，使用 SQLite
- `settings_staging.py`：`DEBUG=False`，使用测试 MySQL
- `settings_production.py`：`DEBUG=False`，使用生产 MySQL，配置白名单

---

## 九、安全与权限设计

### Django-Ninja 特有安全项

| 风险                | 防护措施                                                     |
| ------------------- | ------------------------------------------------------------ |
| **SECRET_KEY 泄露** | 绝不提交到仓库；生产环境通过 systemd `Environment=` 或 `.env` 文件注入 |
| **DEBUG=True 上线** | `settings_production.py` 中强制 `DEBUG=False`；CI 的 `check --deploy` 会检测 |
| **数据库密码暴露**  | 存 Secrets（如果需要在 CI 中连接生产库），否则仅在服务器端配置 |
| **未授权迁移**      | `ENABLE_MIGRATE` 默认 `true`，但生产环境首次部署建议手动执行，确认无误后再开启自动 |
| **依赖投毒**        | `requirements.txt` 锁定版本号（`django-ninja==1.1.0`），避免自动拉取最新版 |

### 模板仓库本身的安全

- **`.env.example` 中所有值留空或标注 `change-me`**，不要放真实密钥
- **在 README 中明确警告**：从模板创建后必须修改 `SECRET_KEY`

---

## 十、使用手册（给模板使用者）

将此段放入模板仓库的 **README.md**：

```markdown
## 🚀 从模板创建后必做（Django-Ninja 后端版）

### 1. 配置仓库变量
进入仓库 **Settings → Secrets and variables → Actions → Variables**，添加：

| 变量名 | 示例值 |
|--------|--------|
| `DEPLOY_SERVER_HOST` | `123.456.78.90` |
| `DEPLOY_FRONTEND_PATH` | `/www/wwwroot/neuramind` |
| `DEPLOY_BACKEND_PATH` | `/www/neuramind` |
| `DEPLOY_VENV_PATH` | `/www/neuramind/venv` |
| `DJANGO_SETTINGS_MODULE` | `neuramind.settings_production` |

### 2. 配置密钥
进入 **Secrets**，添加：

- `SSH_PRIVATE_KEY`：你的服务器私钥（`cat ~/.ssh/id_rsa`）

### 3. 服务器准备（重要）
确保服务器已：
1. 安装 Python 3.11+
2. 创建虚拟环境：`python3 -m venv /www/neuramind/venv`
3. 添加 SSH 公钥授权
4. 创建 systemd 服务文件（见项目 `scripts/neuramind.service` 模板）
5. 配置 Nginx 反向代理到 `127.0.0.1:8000`

### 4. 首次部署
```bash
git push origin main
```

然后去 **Actions** 标签页查看部署状态。首次部署建议观察后端日志：

```bash
sudo journalctl -u neuramind -f
```

### 5. 数据库迁移注意

- 如果项目已有模型变更，首次部署时 CI 会自动执行 `migrate`
- 生产环境数据库建议提前手动备份
- 可通过设置变量 `ENABLE_MIGRATE=false` 关闭自动迁移

```
---

## 十一、完整文件参考

### `scripts/setup-ci.sh`

```bash
#!/bin/bash
echo "=========================================="
echo "  NeuraMind (Django-Ninja) CI 配置向导"
echo "=========================================="
echo ""

read -p "请输入服务器 IP: " HOST
read -p "请输入前端部署路径 (默认: /www/wwwroot/neuramind): " FRONTEND_PATH
FRONTEND_PATH=${FRONTEND_PATH:-/www/wwwroot/neuramind}
read -p "请输入后端部署路径 (默认: /www/neuramind): " BACKEND_PATH
BACKEND_PATH=${BACKEND_PATH:-/www/neuramind}
read -p "请输入虚拟环境路径 (默认: /www/neuramind/venv): " VENV_PATH
VENV_PATH=${VENV_PATH:-/www/neuramind/venv}

echo ""
echo "请在 GitHub 仓库页面手动配置以下 Secrets 和 Variables："
echo ""
echo "【Secrets】"
echo "  SSH_PRIVATE_KEY"
echo ""
echo "【Variables - 必填】"
echo "  DEPLOY_SERVER_HOST = $HOST"
echo "  DEPLOY_FRONTEND_PATH = $FRONTEND_PATH"
echo "  DEPLOY_BACKEND_PATH = $BACKEND_PATH"
echo "  DEPLOY_VENV_PATH = $VENV_PATH"
echo ""
echo "【Variables - 建议配置】"
echo "  DJANGO_SETTINGS_MODULE = neuramind.settings_production"
echo "  ENABLE_MIGRATE = true"
echo "  DEPLOY_RESTART_COMMAND = sudo systemctl restart neuramind"
echo ""
echo "配置完成后，执行 git push 即可触发首次部署。"
echo "=========================================="
```

### `.env.example`

```bash
# Django 核心配置（生产环境通过服务器 systemd 注入，不依赖此文件）
DJANGO_SETTINGS_MODULE=neuramind.settings_development
SECRET_KEY=change-me-in-production-this-is-just-for-local-dev

# 数据库
DATABASE_URL=sqlite:///db.sqlite3
# 生产环境示例：mysql://user:password@127.0.0.1:3306/neuramind

# API 配置
NINJA_DEBUG=True
```

### `scripts/neuramind.service`（systemd 模板）

```ini
[Unit]
Description=NeuraMind Django-Ninja API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/www/neuramind
ExecStart=/www/neuramind/venv/bin/gunicorn neuramind.asgi:application -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000 -w 4
Restart=always
RestartSec=5
Environment="DJANGO_SETTINGS_MODULE=neuramind.settings_production"
Environment="SECRET_KEY=your-production-secret-key-here"
Environment="DATABASE_URL=mysql://user:pass@localhost/neuramind"

[Install]
WantedBy=multi-user.target
```

### `requirements.txt` 示例

```txt
django>=4.2,<5.0
django-ninja==1.1.0
gunicorn==23.0.0
uvicorn[standard]==0.30.0
python-dotenv==1.0.1
# 根据数据库选择：
# psycopg2-binary==2.9.9  # PostgreSQL
# PyMySQL==1.1.0          # MySQL
```

---

## 总结

| 你（模板作者）需要做的                                  | 使用者需要做的                                       |
| ------------------------------------------------------- | ---------------------------------------------------- |
| 写好 `.github/workflows/*.yml`，全部用 `vars`/`secrets` | 在 GitHub 网页填入服务器 IP、路径、虚拟环境位置      |
| 提供 `scripts/neuramind.service` systemd 模板           | 在服务器创建 venv、安装 Python、配置 systemd         |
| 提供 `.env.example` 和配置清单                          | 把 SSH 私钥粘贴到 Secrets，修改生产环境 `SECRET_KEY` |
| 确保 `if:` 条件防止未配置时失败                         | `git push` 触发部署，观察 `journalctl` 日志          |

> **核心思想**：Django-Ninja 是解释型框架，CI 不负责"编译"，而是负责**"传送代码并在服务器上完成环境更新"**。虚拟环境和依赖管理是部署的关键，务必在服务器端预先配置好 `venv`。

---

*归档人：AI 助手*  
*关联文档：TECH-DEV-003《可配置模板仓库 CI/CD 设计指南（通用版）》*  
*技术标签：`模板仓库` `GitHub Actions` `Django-Ninja` `Python` `Vue3` `自动化部署`*