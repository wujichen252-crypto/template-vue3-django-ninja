# API 接口文档

## 基础信息

- **Base URL**: `http://localhost:8000`
- **API Version**: v1
- **认证方式**: Bearer Token (JWT)

## 通用响应格式

```json
{
  "code": 200,
  "data": {},
  "msg": "ok",
  "request_id": "uuid-string"
}
```

## 错误码

| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权/Token无效 |
| 403 | 拒绝访问 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 用户认证

### 注册

**Endpoint**: `POST /api/v1/auth/register`

**Request Body**:
```json
{
  "username": "string",
  "password": "string",
  "email": "string"
}
```

**Response** (201 Created):
```json
{
  "code": 200,
  "data": {
    "id": 1,
    "username": "string",
    "email": "string",
    "avatar_url": null,
    "status": 1,
    "created_at": "2024-01-01T00:00:00Z"
  },
  "msg": "ok",
  "request_id": "uuid-string"
}
```

**Error Responses**:
- 400: 用户名已存在 / 邮箱已被注册 / 参数验证失败

---

### 登录

**Endpoint**: `POST /api/v1/auth/login`

**Request Body**:
```json
{
  "username": "string",
  "password": "string"
}
```

**Response** (200 OK):
```json
{
  "code": 200,
  "data": {
    "access_token": "eyJhbGc...",
    "refresh_token": "eyJhbGc...",
    "expires_in": 7200
  },
  "msg": "ok",
  "request_id": "uuid-string"
}
```

**Error Responses**:
- 401: 用户名或密码错误 / 账号已被禁用

---

### 获取当前用户

**Endpoint**: `GET /api/v1/users/me`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "code": 200,
  "data": {
    "id": 1,
    "username": "string",
    "email": "string",
    "avatar_url": "https://example.com/avatar.jpg",
    "status": 1,
    "created_at": "2024-01-01T00:00:00Z"
  },
  "msg": "ok",
  "request_id": "uuid-string"
}
```

**Error Responses**:
- 401: 未授权 / Token无效/已过期

---

### 刷新 Token

**Endpoint**: `POST /api/v1/auth/refresh`

**Request Body**:
```json
{
  "refresh": "string"
}
```

**Response** (200 OK):
```json
{
  "code": 200,
  "data": {
    "access_token": "eyJhbGc...",
    "refresh_token": "eyJhbGc...",
    "expires_in": 7200
  },
  "msg": "ok",
  "request_id": "uuid-string"
}
```

**Error Responses**:
- 401: 无效的刷新令牌 / 用户不存在

---

## 数据模型

### User

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 用户ID |
| username | string | 用户名（唯一） |
| email | string | 邮箱（唯一） |
| avatar_url | string | 头像URL |
| status | int | 状态（1正常/0禁用） |
| created_at | datetime | 创建时间 |

### Token

| 字段 | 类型 | 说明 |
|------|------|------|
| access_token | string | JWT访问令牌（2小时） |
| refresh_token | string | JWT刷新令牌（7天） |
| expires_in | int | 过期时间（秒） |
