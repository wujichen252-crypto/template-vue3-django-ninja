# 项目工作流

## 开发流程

### 1. 环境准备
- 安装 Python 3.11+
- 安装 Node.js 18+
- 克隆仓库

### 2. 本地开发

#### 前端开发
```bash
cd frontend
npm install
npm run dev
```

#### 后端开发
```bash
cd backend

# 安装 uv（如未安装）
# Windows PowerShell: powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 同步依赖（根据 uv.lock 安装，含开发依赖）
uv sync

# 或仅同步生产依赖
# uv sync --no-dev

cp .env.example .env

# 使用 uv run 运行命令（自动激活虚拟环境）
uv run python manage.py migrate
uv run python manage.py runserver

# 运行测试
uv run pytest

# 代码检查
uv run ruff check .
```

### 3. 代码规范
- 前端：运行 `npm run lint` 检查
- 后端：遵循 PEP 8 规范

### 4. 提交规范
- 使用 Gitmoji 或 conventional commits
- 提交前确保 lint 和测试通过

## 分支管理

### 分支命名
- feature/: 新功能
- fix/: Bug 修复
- hotfix/: 紧急修复
- refactor/: 代码重构
- docs/: 文档更新

### 示例
```
feature/user-authentication
fix/login-validation
hotfix/security-patch
```

## Pull Request 流程

1. 从 main 分支创建新分支
2. 完成开发并测试
3. 填写 PR 模板
4. 提交 PR
5. 等待 Code Review
6. 合并到 main

## 部署流程

### 开发环境
- 自动部署到测试服务器

### 生产环境
1. 创建 release tag
2. 运行测试套件
3. 构建 Docker 镜像
4. 部署到生产服务器
5. 监控运行状态
