# 产品需求文档

## 项目概述

- **项目名称**: template-vue3-django-ninja
- **项目类型**: 前后端分离全栈模板项目
- **核心功能**: 用户认证系统（注册/登录/JWT认证）
- **目标用户**: 开发者，快速启动新项目

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

## 功能需求

### 用户模块

#### 1. 用户注册
- 用户名（唯一，长度 4-32 位）
- 邮箱（唯一，合法邮箱格式）
- 密码（加密存储，bcrypt）
- 返回用户信息

#### 2. 用户登录
- 用户名 + 密码认证
- 返回 Access Token (2小时)
- 返回 Refresh Token (7天)

#### 3. 获取当前用户
- 需要携带 Access Token
- 返回用户详细信息

#### 4. 刷新 Token
- 使用 Refresh Token 换取新的 Access Token

### 权限控制
- 基于 JWT Token 的认证
- 路由守卫（前端）
- API 认证（后端）

## 非功能需求

### 性能
- 前端首屏加载 < 2s
- API 响应时间 < 500ms

### 安全
- 密码 bcrypt 加密存储
- JWT Token 时效性
- 防止 SQL 注入
- 防止 XSS 攻击

### 可维护性
- 代码分层（Handler/Service/Model）
- 统一响应格式
- 统一错误处理
- JSON 格式日志

## 项目结构

```
template-vue3-django-ninja/
├── frontend/          # Vue3 前端
├── backend/           # Django-Ninja 后端
├── docs/              # 项目文档
├── .trae/rules/       # AI 规则文件
└── .github/           # GitHub 配置
```
