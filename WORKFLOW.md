# 项目工作流指南

本文档详细说明项目的完整开发、测试、部署工作流。

## 📋 目录

1. [分支策略](#分支策略)
2. [开发流程](#开发流程)
3. [代码审查](#代码审查)
4. [CI/CD 流程](#cicd-流程)
5. [发布流程](#发布流程)
6. [故障处理](#故障处理)

---

## 分支策略

### 分支模型

```
main (生产分支)
  ↑
develop (开发分支)
  ↑
feature/* (功能分支)
fix/* (修复分支)
hotfix/* (热修复分支)
```

### 分支命名规范

| 类型 | 命名格式 | 示例 |
|------|----------|------|
| 功能 | `feature/<功能名>` | `feature/user-authentication` |
| 修复 | `fix/<问题描述>` | `fix/login-validation` |
| 热修复 | `hotfix/<问题描述>` | `hotfix/security-patch` |
| 重构 | `refactor/<描述>` | `refactor/api-structure` |
| 文档 | `docs/<描述>` | `docs/api-guide` |
| 性能 | `perf/<描述>` | `perf/query-optimization` |

### 保护规则

- `main`: 禁止直接推送，必须通过 PR 合并
- `develop`: 禁止直接推送，必须通过 PR 合并
- 所有 PR 必须通过 CI 检查
- 所有 PR 必须至少 1 人审查通过

---

## 开发流程

### 1. 开始新功能

```bash
# 从 develop 分支创建功能分支
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name

# 进行开发工作
git add .
git commit -m "feat: 添加新功能"

# 推送分支
git push -u origin feature/your-feature-name
```

### 2. 提交规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型说明：**

| 类型 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(auth): 添加登录功能` |
| `fix` | Bug 修复 | `fix(api): 修复空指针异常` |
| `docs` | 文档更新 | `docs(readme): 更新部署说明` |
| `style` | 代码格式 | `style(frontend): 格式化代码` |
| `refactor` | 重构 | `refactor(backend): 优化查询逻辑` |
| `perf` | 性能优化 | `perf(cache): 提升缓存命中率` |
| `test` | 测试相关 | `test(auth): 添加登录测试` |
| `chore` | 构建/工具 | `chore(deps): 更新依赖` |
| `ci` | CI/CD 变更 | `ci(github): 添加部署工作流` |

### 3. 开发检查清单

- [ ] 代码符合项目规范
- [ ] 已添加单元测试
- [ ] 已添加集成测试
- [ ] 所有测试通过
- [ ] 代码覆盖率 ≥ 80%
- [ ] 已更新文档
- [ ] 已进行本地测试

---

## 代码审查

### 创建 PR

1. 在 GitHub 上创建 PR
2. 填写完整的 PR 模板
3. 关联相关 Issue
4. 请求审查者

### 审查检查清单

**审查者职责：**

- [ ] 代码逻辑正确
- [ ] 符合编码规范
- [ ] 测试覆盖充分
- [ ] 无安全漏洞
- [ ] 性能影响评估
- [ ] 文档已更新

### 审查流程

```
开发者提交 PR
    ↓
自动运行 CI 检查
    ↓
代码审查
    ↓
修改问题（如有）
    ↓
审查通过
    ↓
合并到目标分支
```

---

## CI/CD 流程

### 持续集成 (CI)

**触发条件：**
- Push 到 `main` 或 `develop` 分支
- Pull Request 到 `main` 分支

**执行步骤：**

#### 前端检查
1. 安装依赖 (`pnpm install`)
2. ESLint 检查
3. TypeScript 类型检查
4. 单元测试 + 覆盖率
5. 生产构建

#### 后端检查
1. 启动 PostgreSQL 和 Redis 服务
2. 安装依赖 (`pip install`)
3. 数据库迁移
4. Django 系统检查
5. 单元测试 + 覆盖率
6. 性能测试
7. 覆盖率门槛检查 (≥80%)

#### 集成测试
1. API 集成测试
2. 限流测试
3. 缓存集成测试

#### 安全检查
1. Bandit Python 安全扫描
2. Safety 依赖漏洞检查
3. npm audit 安全审计

### 持续部署 (CD)

#### 测试环境部署

**触发条件：**
- Push 到 `develop` 分支
- 手动触发（选择 staging）

**部署流程：**
1. 构建前端静态文件
2. 构建后端 Docker 镜像
3. 部署到测试服务器
4. 执行数据库迁移
5. 健康检查

#### 生产环境部署

**触发条件：**
- 推送版本标签 (`v*`)
- 手动触发（选择 production）

**部署流程（蓝绿部署）：**
1. 创建 GitHub Release
2. 备份数据库
3. 构建并推送 Docker 镜像
4. 部署前端静态文件
5. 启动新容器（蓝色）
6. 健康检查
7. 切换流量到蓝色
8. 停止旧容器（绿色）
9. 执行数据库迁移
10. 最终健康检查

---

## 发布流程

### 版本号规范

使用 [语义化版本](https://semver.org/lang/zh-CN/) (SemVer)：

```
主版本号.次版本号.修订号
```

- **主版本号**：不兼容的 API 修改
- **次版本号**：向下兼容的功能新增
- **修订号**：向下兼容的问题修复

### 发布步骤

#### 1. 准备发布

```bash
# 切换到 main 分支
git checkout main
git pull origin main

# 创建发布分支（可选）
git checkout -b release/v1.2.0
```

#### 2. 更新版本号

```bash
# 前端版本
# 更新 frontend/package.json 中的 version

# 后端版本
# 更新 backend/pyproject.toml 或 backend/__init__.py 中的版本
```

#### 3. 更新 CHANGELOG

```bash
# 生成变更日志
git log --pretty=format:"- %s" v1.1.0..HEAD > CHANGELOG.md
```

#### 4. 提交变更

```bash
git add .
git commit -m "chore(release): 准备 v1.2.0 发布"
git push origin release/v1.2.0
```

#### 5. 创建 PR

创建 PR 从 `release/v1.2.0` 到 `main`

#### 6. 合并并打标签

```bash
# PR 合并后，在 main 分支打标签
git checkout main
git pull origin main
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin v1.2.0
```

#### 7. 自动发布

推送标签后，自动触发：
1. 创建 GitHub Release
2. 生成变更日志
3. 构建并上传产物
4. 部署到生产环境
5. 发送通知

---

## 故障处理

### 回滚流程

#### 前端回滚

```bash
# 回滚到上一个版本
git checkout <上一个稳定版本的 commit>

# 重新构建并部署
pnpm install
pnpm run build
# 部署静态文件
```

#### 后端回滚

```bash
# 使用 Docker 回滚
ssh user@server "
  cd /opt/app &&
  docker-compose -f docker-compose.production.yml down &&
  docker-compose -f docker-compose.production.yml up -d backend-green &&
  docker-compose -f docker-compose.production.yml stop backend-blue
"
```

#### 数据库回滚

```bash
# 恢复备份
pg_restore -h localhost -U postgres -d template_db /backup/db_YYYYMMDD_HHMMSS.sql
```

### 紧急修复流程

1. 从 `main` 创建 `hotfix/<问题>` 分支
2. 修复问题
3. 创建 PR 到 `main` 和 `develop`
4. 审查并合并
5. 打补丁版本标签（如 `v1.2.1`）
6. 自动部署

---

## 环境配置

### 必需的环境变量

#### GitHub Secrets

| 名称 | 说明 | 必需 |
|------|------|------|
| `DOCKERHUB_TOKEN` | Docker Hub 访问令牌 | 是 |
| `STAGING_SSH_KEY` | 测试环境 SSH 密钥 | 是 |
| `PRODUCTION_SSH_KEY` | 生产环境 SSH 密钥 | 是 |
| `SLACK_WEBHOOK_URL` | Slack 通知 Webhook | 否 |
| `CODECOV_TOKEN` | Codecov 令牌 | 否 |

#### GitHub Variables

| 名称 | 说明 | 默认值 |
|------|------|--------|
| `DOCKERHUB_USERNAME` | Docker Hub 用户名 | - |
| `STAGING_HOST` | 测试环境主机 | - |
| `STAGING_USER` | 测试环境用户 | - |
| `PRODUCTION_HOST` | 生产环境主机 | - |
| `PRODUCTION_USER` | 生产环境用户 | - |
| `PROJECT_FRONTEND_DIR` | 前端目录 | `./frontend` |
| `PROJECT_BACKEND_DIR` | 后端目录 | `./backend` |
| `PYTHON_VERSION` | Python 版本 | `3.11` |
| `NODE_VERSION` | Node.js 版本 | `20` |

---

## 工具和资源

### 本地开发工具

- **Act**: 本地运行 GitHub Actions
  ```bash
  brew install act
  act -j frontend-check
  ```

### 监控和日志

- GitHub Actions 日志：Actions 标签页
- Codecov：代码覆盖率报告
- Docker Hub：镜像仓库

### 文档

- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)

---

## 常见问题

### Q: CI 检查失败怎么办？

A: 查看 Actions 日志，修复问题后重新推送。

### Q: 如何跳过 CI？

A: 在 commit message 中添加 `[skip ci]`：
```bash
git commit -m "docs: 更新文档 [skip ci]"
```

### Q: 如何手动触发部署？

A: 在 Actions 标签页选择 Deploy 工作流，点击 "Run workflow"。

### Q: 代码覆盖率不达标怎么办？

A: 添加更多测试用例，确保覆盖所有分支和边界条件。

---

## 联系方式

如有问题，请联系：

- **开发团队**: dev-team@example.com
- **运维团队**: ops-team@example.com
- **Slack**: #dev-channel
