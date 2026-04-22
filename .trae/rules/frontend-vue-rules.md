# 前端 Vue3 规则文件

## 技术栈
- Vue 3.4 + TypeScript + Vite
- Pinia (状态管理)
- Vue Router 4
- Axios (HTTP 客户端)
- Tailwind CSS
- Element Plus

## 代码规范

### 组件规范
- 使用 `<script setup>` + Composition API
- 组件文件使用 PascalCase 命名
- 组件应该保持单一职责

### 样式规范
- 使用 Tailwind CSS 工具类
- 配色方案：黑白极简主题
  - 主色：#000000 (黑)
  - 背景：#FFFFFF (白)
  - 浅灰：#F5F5F5
  - 强调色：#2563EB (蓝)

### 性能优化
- 图片懒加载
- 路由懒加载
- 组件异步导入
- 使用 `defineAsyncComponent`

### 命名规范
- 组件：PascalCase (如: AppHeader.vue)
- 变量/函数：camelCase
- 常量：UPPER_SNAKE_CASE
- 类型定义：PascalCase

## 项目结构

```
frontend/src/
├── api/          # API 接口封装
├── assets/       # 静态资源
├── components/   # 公共组件
├── composables/  # 组合式函数
├── router/       # 路由配置
├── stores/       # Pinia 状态
├── types/        # TypeScript 类型
├── utils/        # 工具函数
└── views/        # 页面组件
```

## API 调用
- 使用 Axios 封装请求
- 统一错误处理
- Token 自动注入
