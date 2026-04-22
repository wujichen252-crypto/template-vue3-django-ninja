# API 文档规范

## 接口响应格式

### 成功响应
```json
{
  "code": 200,
  "data": {},
  "msg": "ok",
  "request_id": "uuid-string"
}
```

### 错误响应
```json
{
  "code": 400,
  "data": null,
  "msg": "错误信息",
  "request_id": "uuid-string"
}
```

## 用户模块 API

### 注册
- URL: `POST /api/v1/auth/register`
- Request:
```json
{
  "username": "string",
  "password": "string",
  "email": "string"
}
```
- Response:
```json
{
  "code": 200,
  "data": {
    "id": 1,
    "username": "string",
    "email": "string",
    "avatar_url": "string",
    "status": 1,
    "created_at": "2024-01-01T00:00:00Z"
  },
  "msg": "ok"
}
```

### 登录
- URL: `POST /api/v1/auth/login`
- Request:
```json
{
  "username": "string",
  "password": "string"
}
```
- Response:
```json
{
  "code": 200,
  "data": {
    "access_token": "string",
    "refresh_token": "string",
    "expires_in": 7200
  },
  "msg": "ok"
}
```

### 获取当前用户
- URL: `GET /api/v1/users/me`
- Headers: `Authorization: Bearer <access_token>`
- Response:
```json
{
  "code": 200,
  "data": {
    "id": 1,
    "username": "string",
    "email": "string",
    "avatar_url": "string",
    "status": 1,
    "created_at": "2024-01-01T00:00:00Z"
  },
  "msg": "ok"
}
```

### 刷新 Token
- URL: `POST /api/v1/auth/refresh`
- Request:
```json
{
  "refresh": "string"
}
```
- Response:
```json
{
  "code": 200,
  "data": {
    "access_token": "string",
    "refresh_token": "string",
    "expires_in": 7200
  },
  "msg": "ok"
}
```

## 错误码

| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 拒绝访问 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
