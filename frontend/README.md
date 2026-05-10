# AutoResearcher Frontend - API 接口文档

## 项目概述

AutoResearcher 前端是基于 **Vue 3 + Vite** 构建的 AI 聊天应用，支持与后端 Go 服务进行通信，实现用户认证、多会话管理和 AI 对话功能。

## 技术栈

- **核心框架**: Vue 3 (Composition API)
- **构建工具**: Vite
- **状态管理**: Pinia
- **路由管理**: Vue Router
- **UI 组件库**: Element Plus
- **HTTP 客户端**: Axios
- **Markdown 渲染**: markdown-it

## 后端接口需求文档

### 1. 认证模块 (Authentication)

#### 1.1 用户注册
```
POST /api/auth/register
```

**请求参数**:
```json
{
  "username": "string (required, 3-20 字符)",
  "password": "string (required, 最少 6 字符)"
}
```

**成功响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "user": {
      "user_id": 1,
      "username": "testuser"
    }
  }
}
```

---

#### 1.2 用户登录
```
POST /api/auth/login
```

**请求参数**:
```json
{
  "username": "string (required)",
  "password": "string (required)"
}
```

**成功响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "token": "JWT_TOKEN_STRING",
    "user": {
      "user_id": 1,
      "username": "testuser"
    }
  }
}
```

**说明**: 
- `token` 是 JWT 格式，前端会存储在 localStorage 中
- 后续请求需要在 Header 中携带：`Authorization: Bearer {token}`

---

#### 1.3 退出登录
```
POST /api/auth/logout
```

**请求头**:
```
Authorization: Bearer {token}
```

**成功响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": null
}
```

---

#### 1.4 获取用户信息
```
GET /api/auth/:userId
```

**请求头**:
```
Authorization: Bearer {token}
```

**成功响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "user_id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "created_at": "2026-05-09T00:00:00Z"
  }
}
```

---

### 2. 会话管理模块 (Session Management)

#### 2.1 获取会话列表
```
GET /api/chat/sessions
```

**请求头**:
```
Authorization: Bearer {token}
```

**成功响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "title": "会话标题 1",
      "created_at": "2026-05-09T10:00:00Z",
      "updated_at": "2026-05-09T12:00:00Z"
    },
    {
      "id": 2,
      "title": "会话标题 2",
      "created_at": "2026-05-09T11:00:00Z",
      "updated_at": "2026-05-09T13:00:00Z"
    }
  ]
}
```

---

#### 2.2 创建新会话
```
POST /api/chat/sessions
```

**请求头**:
```
Authorization: Bearer {token}
```

**请求参数**:
```json
{
  "title": "会话标题 (可选，默认'新会话')"
}
```

**成功响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 3,
    "title": "新会话",
    "created_at": "2026-05-09T14:00:00Z",
    "updated_at": "2026-05-09T14:00:00Z"
  }
}
```

---

#### 2.3 删除会话
```
DELETE /api/chat/sessions/:sessionId
```

**请求头**:
```
Authorization: Bearer {token}
```

**成功响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": null
}
```

---

#### 2.4 获取会话消息
```
GET /api/chat/sessions/:sessionId/messages
```

**请求头**:
```
Authorization: Bearer {token}
```

**成功响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "role": "user",
      "content": "你好，请帮我解释一下机器学习",
      "created_at": "2026-05-09T10:00:00Z"
    },
    {
      "id": 2,
      "role": "assistant",
      "content": "机器学习是人工智能的一个分支...",
      "created_at": "2026-05-09T10:00:05Z"
    }
  ]
}
```

**说明**:
- `role` 字段：`user` (用户) 或 `assistant` (AI)
- `content` 字段支持 Markdown 格式

---

### 3. 聊天消息模块 (Chat Messages)

#### 3.1 发送消息 (重要：需要支持 SSE 流式响应)
```
POST /api/chat/send
```

**请求头**:
```
Authorization: Bearer {token}
Content-Type: application/json
```

**请求参数**:
```json
{
  "session_id": 1,
  "content": "请帮我解释深度学习"
}
```

**成功响应 (SSE 流式)**:
```
Content-Type: text/event-stream

data: {"type": "thinking", "content": "正在思考..."}

data: {"type": "content", "content": "深度"}

data: {"type": "content", "content": "学习"}

data: {"type": "content", "content": "是"}

data: {"type": "content", "content": "机器"}

data: {"type": "content", "content": "学习"}

data: {"type": "content", "content": "的"}

data: {"type": "content", "content": "一个"}

data: {"type": "content", "content": "分支"}

data: {"type": "done", "content": "完整回复内容"}
```

**或者普通响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 3,
    "role": "assistant",
    "content": "深度学习是机器学习的一个分支...",
    "created_at": "2026-05-09T14:00:00Z"
  }
}
```

**说明**:
- **推荐使用 SSE (Server-Sent Events) 实现流式输出**，提升用户体验
- 前端会监听 `text/event-stream`，实时显示 AI 的思考过程和回复内容
- 如果暂时不支持 SSE，可以先返回完整响应，前端会正常显示

---

### 4. 文件管理模块 (File Management)

#### 4.1 获取文件列表
```
GET /api/chat/sessions/:sessionId/files
```

**请求头**:
```
Authorization: Bearer {token}
```

**成功响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "name": "experiment_results.py",
      "size": "2.5 KB",
      "type": "python",
      "created_at": "2026-05-09T10:00:00Z"
    },
    {
      "id": 2,
      "name": "data_analysis.ipynb",
      "size": "15.3 KB",
      "type": "notebook",
      "created_at": "2026-05-09T11:00:00Z"
    }
  ]
}
```

---

#### 4.2 下载文件
```
GET /api/chat/files/:fileId
```

**请求头**:
```
Authorization: Bearer {token}
```

**成功响应**:
- Content-Type: `application/octet-stream`
- Content-Disposition: `attachment; filename="filename.ext"`
- 返回文件二进制流

---

## 错误响应格式

所有接口在出错时应返回统一格式：

```json
{
  "code": 400,
  "message": "错误描述信息",
  "data": null
}
```

**常见错误码**:
- `400`: 请求参数错误
- `401`: 未授权（token 无效或过期）
- `403`: 禁止访问
- `404`: 资源不存在
- `500`: 服务器内部错误

---

## 跨域配置 (CORS)

后端需要配置 CORS 允许前端跨域访问：

```go
// 允许的源
Access-Control-Allow-Origin: http://localhost:3000

// 允许的方法
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS

// 允许的头部
Access-Control-Allow-Headers: Content-Type, Authorization

// 允许携带凭证
Access-Control-Allow-Credentials: true
```

---

## 开发环境配置

### 前端启动
```bash
cd frontend
npm install
npm run dev
```

前端默认运行在：`http://localhost:3000`

### 后端启动
```bash
cd backend
go run main.go
```

后端默认运行在：`http://localhost:8080`

### 代理配置

`vite.config.js` 中已配置代理：
```javascript
server: {
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://localhost:8080',
      changeOrigin: true
    }
  }
}
```

前端请求 `/api/*` 会自动代理到后端 `http://localhost:8080/api/*`

---

## 前端目录结构

```
frontend/
├── src/
│   ├── api/              # API 接口模块
│   │   ├── auth.js       # 认证相关接口
│   │   └── chat.js       # 聊天相关接口
│   ├── assets/           # 静态资源
│   ├── components/       # 公共组件
│   ├── router/           # 路由配置
│   │   └── index.js
│   ├── stores/           # Pinia 状态管理
│   │   ├── user.js       # 用户状态
│   │   └── chat.js       # 聊天状态
│   ├── utils/            # 工具函数
│   │   └── request.js    # Axios 封装
│   ├── views/            # 页面组件
│   │   ├── Login.vue     # 登录页
│   │   ├── Register.vue  # 注册页
│   │   └── Chat.vue      # 聊天主页
│   ├── App.vue           # 根组件
│   ├── main.js           # 入口文件
│   └── style.css         # 全局样式
├── index.html
├── package.json
├── vite.config.js
└── README.md
```

---

## 功能特性

### 1. 用户认证
- ✅ 登录/注册页面
- ✅ JWT Token 自动管理
- ✅ 路由守卫（未登录跳转）
- ✅ 退出登录

### 2. 聊天功能
- ✅ 多会话管理（左侧边栏）
- ✅ 消息列表展示
- ✅ Markdown 渲染（支持代码高亮）
- ✅ 发送消息（支持 Ctrl+Enter 快捷键）
- ✅ AI 思考状态指示器
- ✅ 自动滚动到最新消息

### 3. 文件管理
- ✅ 文件列表展示（右侧边栏）
- ✅ 文件下载功能
- ✅ 可收起/展开的侧边栏

### 4. 响应式设计
- ✅ 左右侧边栏可折叠
- ✅ 自适应布局
- ✅ 优雅的 UI 交互

---

## 待实现功能（需要后端支持）

1. **SSE 流式响应**: AI 回复内容实时流式传输
2. **文件上传**: 支持用户上传文件给 AI 分析
3. **代码执行**: 在沙箱环境中执行 AI 生成的代码
4. **论文检索**: 集成 arXiv 等学术搜索
5. **RAG 功能**: 基于向量数据库的论文检索

---

## 联系方式

如有接口问题或需要调整，请联系后端开发团队。
