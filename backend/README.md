# AutoResearcher 后端开发指南

## 项目结构

```
backend/
├── cmd/
│   └── server/
│       └── main.go              # 程序入口
├── internal/
│   ├── config/                  # 配置文件
│   │   └── config.go
│   ├── models/                  # 数据模型
│   │   ├── user.go
│   │   ├── session.go
│   │   └── message.go
│   ├── handlers/                # HTTP 处理器
│   │   ├── auth.go              # 认证相关
│   │   ├── chat.go              # 聊天相关
│   │   └── health.go            # 健康检查
│   ├── middleware/              # 中间件
│   │   ├── auth.go              # JWT 认证
│   │   ├── cors.go              # 跨域处理
│   │   └── logger.go            # 日志记录
│   ├── routes/                  # 路由配置
│   │   └── router.go
│   ├── services/                # 业务逻辑层
│   │   ├── auth_service.go
│   │   ├── chat_service.go
│   │   └── agent_service.go     # AI Agent 调用
│   ├── utils/                   # 工具函数
│   │   ├── jwt.go
│   │   ├── password.go
│   │   └── response.go          # 统一响应格式
│   └── database/                # 数据库相关
│       ├── db.go
│       └── migrations/
├── pkg/                         # 可复用包
│   └── logger/
├── api/                         # API 文档 (Swagger)
├── scripts/                     # 脚本文件
├── tests/                       # 测试文件
├── .env                         # 环境变量
├── .gitignore
├── go.mod
├── go.sum
└── Makefile
```

## 技术栈

- **Go (Golang)** - 高性能后端语言
- **Gin** - Web 框架
- **GORM** - ORM 库
- **PostgreSQL/MySQL** - 关系型数据库
- **Redis** - 缓存与会话存储
- **JWT** - 身份认证
- **Docker** - 容器化部署

## 快速开始

### 1. 安装依赖

```bash
cd backend
go mod download
```

### 2. 配置环境变量

复制 `.env.example` 到 `.env` 并修改配置：

```bash
cp .env.example .env
```

### 3. 启动开发服务器

```bash
go run cmd/server/main.go
```

服务将在 `http://localhost:8080` 启动

### 4. 构建生产版本

```bash
go build -o server cmd/server/main.go
```

### 5. 运行测试

```bash
go test ./...
```

## API 接口文档

### 基础信息

- **Base URL**: `http://localhost:8080/api`
- **认证方式**: JWT Token (Bearer Token)
- **响应格式**: 统一返回 JSON 格式

#### 响应格式规范

所有接口统一返回以下格式：

```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

- **code**: 状态码
  - `200`: 操作成功
  - `400`: 请求参数错误
  - `401`: 未授权/Token 过期
  - `403`: 禁止访问
  - `404`: 资源不存在
  - `500`: 服务器内部错误
- **message**: 操作结果描述，错误时会包含具体错误信息
- **data**: 成功时返回的数据对象

---

### 认证模块 (Authentication)

#### 1. 用户注册

```http
POST /api/auth/register
Content-Type: application/json

请求体:
{
  "username": "string",     // 必填，用户名
  "password": "string"      // 必填，密码
}

成功响应 (200):
{
  "code": 200,
  "message": "注册成功",
  "data": {
    "token": "jwt_token_string",
    "user": {
      "id": 1,
      "username": "string",
      "created_at": "2024-01-01T00:00:00Z"
    }
  }
}

失败响应 (400):
{
  "code": 400,
  "message": "用户名已存在",
  "data": null
}
```

#### 2. 用户登录

```http
POST /api/auth/login
Content-Type: application/json

请求体:
{
  "username": "string",     // 必填
  "password": "string"      // 必填
}

成功响应 (200):
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "token": "jwt_token_string",
    "user": {
      "id": 1,
      "username": "string"
    }
  }
}

失败响应 (401):
{
  "code": 401,
  "message": "用户名或密码错误",
  "data": null
}
```

#### 3. 用户登出

```http
POST /api/auth/logout
Authorization: Bearer {token}

成功响应 (200):
{
  "code": 200,
  "message": "登出成功",
  "data": null
}
```

#### 4. 获取当前用户信息

```http
GET /api/auth/me
Authorization: Bearer {token}

成功响应 (200):
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "username": "string",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

---

### 聊天模块 (Chat)

#### 1. 发送消息 (SSE 流式)

```http
POST /api/chat/stream
Content-Type: application/json
Authorization: Bearer {token}

请求体:
{
  "message": "string",      // 必填，用户消息内容
  "session_id": "string"    // 可选，会话 ID，不传则创建新会话
}

响应格式: SSE (Server-Sent Events)
Content-Type: text/event-stream

流式数据:
data: {"content": "你", "type": "token"}
data: {"content": "好", "type": "token"}
data: {"content": "！", "type": "token"}
data: [DONE]

错误响应 (在流开始前返回):
{
  "code": 400,
  "message": "消息内容不能为空",
  "data": null
}

其他错误码:
- 401: 未授权，请先登录
- 500: 服务器内部错误
```

#### 2. 获取会话列表

```http
GET /api/chat/sessions
Authorization: Bearer {token}

成功响应 (200):
{
  "code": 200,
  "message": "success",
  "data": {
    "sessions": [
      {
        "id": "123",
        "title": "新对话",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
      }
    ]
  }
}

失败响应 (401):
{
  "code": 401,
  "message": "未授权，请先登录",
  "data": null
}
```

#### 3. 获取会话历史消息

```http
GET /api/chat/history/{session_id}
Authorization: Bearer {token}

成功响应 (200):
{
  "code": 200,
  "message": "success",
  "data": {
    "messages": [
      {
        "id": 1,
        "role": "user",
        "content": "你好",
        "timestamp": "2024-01-01T00:00:00Z"
      },
      {
        "id": 2,
        "role": "assistant",
        "content": "你好！有什么可以帮助你的？",
        "timestamp": "2024-01-01T00:00:01Z"
      }
    ]
  }
}

失败响应 (404):
{
  "code": 404,
  "message": "会话不存在",
  "data": null
}
```

#### 4. 创建新会话

```http
POST /api/chat/sessions
Authorization: Bearer {token}

请求体 (可选):
{
  "title": "string"    // 可选，会话标题，不传则使用默认标题
}

成功响应 (200):
{
  "code": 200,
  "message": "创建成功",
  "data": {
    "session_id": "123"
  }
}
```

#### 5. 删除会话

```http
DELETE /api/chat/sessions/{session_id}
Authorization: Bearer {token}

成功响应 (200):
{
  "code": 200,
  "message": "删除成功",
  "data": null
}

失败响应 (404):
{
  "code": 404,
  "message": "会话不存在",
  "data": null
}
```

#### 6. 更新会话标题

```http
PUT /api/chat/sessions/{session_id}
Authorization: Bearer {token}
Content-Type: application/json

请求体:
{
  "title": "string"    // 必填，新的会话标题
}

成功响应 (200):
{
  "code": 200,
  "message": "更新成功",
  "data": null
}
```

---

### AI Agent 模块 (可选，根据实际需求)

#### 1. 执行研究任务

```http
POST /api/agent/research
Authorization: Bearer {token}
Content-Type: application/json

请求体:
{
  "task": "string",           // 必填，研究任务描述
  "session_id": "string"      // 可选，关联的会话 ID
}

响应格式: SSE (Server-Sent Events)
Content-Type: text/event-stream

流式数据:
data: {"type": "planning", "content": "正在规划任务..."}
data: {"type": "search", "content": "正在搜索文献..."}
data: {"type": "rag", "content": "正在解析论文..."}
data: {"type": "code", "content": "正在生成代码..."}
data: {"type": "result", "content": "任务完成"}
data: [DONE]
```

---

### 健康检查模块

#### 1. 健康检查

```http
GET /api/health

成功响应 (200):
{
  "code": 200,
  "message": "success",
  "data": {
    "status": "healthy",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

---

### 统一错误码规范

| Code | 说明 | 处理建议 |
|------|------|----------|
| 200 | 操作成功 | - |
| 400 | 请求参数错误 | 检查请求参数格式 |
| 401 | 未授权/Token 过期 | 跳转登录页或刷新 Token |
| 403 | 禁止访问 | 检查权限 |
| 404 | 资源不存在 | 检查资源 ID |
| 500 | 服务器内部错误 | 联系管理员 |

---

## 数据库设计

### 用户表 (users)

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 会话表 (sessions)

```sql
CREATE TABLE sessions (
    id VARCHAR(64) PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    title VARCHAR(255) DEFAULT '新对话',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 消息表 (messages)

```sql
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,  -- 'user' 或 'assistant'
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 索引建议

```sql
-- 用户表索引
CREATE INDEX idx_users_username ON users(username);

-- 会话表索引
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_created_at ON sessions(created_at);

-- 消息表索引
CREATE INDEX idx_messages_session_id ON messages(session_id);
CREATE INDEX idx_messages_timestamp ON messages(timestamp);
```

---

## 环境变量配置

创建 `.env` 文件：

```env
# 服务器配置
PORT=8080
GIN_MODE=release

# JWT 配置
JWT_SECRET=your_secret_key
JWT_EXPIRE=24h

# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=password
DB_NAME=autoresearcher

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379

# AI 服务配置
AI_SERVICE_URL=http://localhost:5000

# 跨域配置
CORS_ALLOW_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

---

## 开发注意事项

### 1. JWT 认证实现

- Token 有效期建议设置为 24 小时
- 实现 Refresh Token 机制（可选）
- Token 存储在请求头：`Authorization: Bearer {token}`

示例 JWT 实现：

```go
// 生成 Token
func GenerateToken(userID uint, username string) (string, error) {
    claims := jwt.MapClaims{
        "user_id":  userID,
        "username": username,
        "exp":      time.Now().Add(24 * time.Hour).Unix(),
    }
    token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
    return token.SignedString([]byte(jwtSecret))
}

// 解析 Token
func ParseToken(tokenString string) (jwt.MapClaims, error) {
    token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
        return []byte(jwtSecret), nil
    })
    if err != nil {
        return nil, err
    }
    return token.Claims.(jwt.MapClaims), nil
}
```

### 2. SSE 流式响应实现要点

设置响应头：

```go
w.Header().Set("Content-Type", "text/event-stream")
w.Header().Set("Cache-Control", "no-cache")
w.Header().Set("Connection", "keep-alive")
w.Header().Set("Access-Control-Allow-Origin", "*")
```

使用 `http.Flusher` 接口实现实时推送：

```go
flusher, ok := w.(http.Flusher)
if !ok {
    http.Error(w, "Streaming unsupported", http.StatusInternalServerError)
    return
}

// 发送数据
fmt.Fprintf(w, "data: %s\n\n", jsonData)
flusher.Flush()

// 发送结束标记
fmt.Fprintf(w, "data: [DONE]\n\n")
flusher.Flush()
```

### 3. 中间件实现

#### JWT 认证中间件

```go
func AuthMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        token := c.GetHeader("Authorization")
        if token == "" {
            c.JSON(http.StatusUnauthorized, gin.H{
                "code": 401,
                "myMessage.sql": "未授权，请先登录",
                "data": nil,
            })
            c.Abort()
            return
        }
        
        // 去掉 "Bearer " 前缀
        token = strings.TrimPrefix(token, "Bearer ")
        
        // 验证 Token
        claims, err := ParseToken(token)
        if err != nil {
            c.JSON(http.StatusUnauthorized, gin.H{
                "code": 401,
                "myMessage.sql": "Token 无效或已过期",
                "data": nil,
            })
            c.Abort()
            return
        }
        
        // 将用户信息存入上下文
        c.Set("user_id", claims["user_id"])
        c.Set("username", claims["username"])
        c.Next()
    }
}
```

#### CORS 中间件

```go
func CORSMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        c.Writer.Header().Set("Access-Control-Allow-Origin", "*")
        c.Writer.Header().Set("Access-Control-Allow-Credentials", "true")
        c.Writer.Header().Set("Access-Control-Allow-Headers", "Content-Type, Content-Length, Accept-Encoding, X-CSRF-Token, Authorization, accept, origin, Cache-Control, X-Requested-With")
        c.Writer.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS, GET, PUT, DELETE")
        
        if c.Request.Method == "OPTIONS" {
            c.AbortWithStatus(http.StatusNoContent)
            return
        }
        
        c.Next()
    }
}
```

### 4. 统一响应格式

```go
type Response struct {
    Code    int         `json:"code"`
    Message string      `json:"myMessage.sql"`
    Data    interface{} `json:"data"`
}

func Success(c *gin.Context, data interface{}) {
    c.JSON(http.StatusOK, Response{
        Code:    200,
        Message: "success",
        Data:    data,
    })
}

func Error(c *gin.Context, code int, message string) {
    c.JSON(http.StatusOK, Response{
        Code:    code,
        Message: message,
        Data:    nil,
    })
}
```

### 5. 密码加密

```go
// 加密密码
func HashPassword(password string) (string, error) {
    bytes, err := bcrypt.GenerateFromPassword([]byte(password), 14)
    return string(bytes), err
}

// 验证密码
func CheckPasswordHash(password, hash string) bool {
    err := bcrypt.CompareHashAndPassword([]byte(hash), []byte(password))
    return err == nil
}
```

---

## 部署

### Docker 部署

创建 `Dockerfile`：

```dockerfile
FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o server cmd/server/main.go

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/
COPY --from=builder /app/server .
COPY --from=builder /app/.env .

EXPOSE 8080
CMD ["./server"]
```

构建和运行：

```bash
docker build -t autoresearcher-backend .
docker run -p 8080:8080 autoresearcher-backend
```

### Docker Compose 部署

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8080:8080"
    environment:
      - DB_HOST=db
      - REDIS_HOST=redis
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: autoresearcher
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

启动：

```bash
docker-compose up -d
```

---

## 测试

### 单元测试示例

```go
package handlers

import (
    "testing"
    "net/http"
    "net/http/httptest"
    "github.com/gin-gonic/gin"
)

func TestHealthCheck(t *testing.T) {
    gin.SetMode(gin.TestMode)
    
    w := httptest.NewRecorder()
    c, _ := gin.CreateTestContext(w)
    
    HealthCheck(c)
    
    assert.Equal(t, http.StatusOK, w.Code)
    assert.Contains(t, w.Body.String(), "healthy")
}
```

运行测试：

```bash
go test -v ./...
```

---

## 常见问题

### Q: 如何修改服务器端口？
A: 修改 `.env` 文件中的 `PORT` 配置

### Q: SSE 连接断开怎么办？
A: 检查网络稳定性，实现客户端重连机制

### Q: 如何处理大量并发请求？
A: 使用 Goroutine 池和连接池，优化数据库查询

### Q: Token 过期如何处理？
A: 实现 Refresh Token 机制或引导用户重新登录

---

## 性能优化建议

1. **数据库优化**
   - 使用连接池
   - 添加合适的索引
   - 使用预编译语句

2. **缓存策略**
   - 使用 Redis 缓存热点数据
   - 实现会话级别的缓存

3. **并发处理**
   - 使用 Goroutine 处理异步任务
   - 使用 Channels 进行协程通信

4. **限流与降级**
   - 实现请求频率限制
   - 实现服务降级策略

---

## 安全建议

1. **密码安全**
   - 使用 bcrypt 加密存储密码
   - 强制密码复杂度要求

2. **Token 安全**
   - 设置合理的 Token 过期时间
   - 实现 Token 黑名单机制

3. **请求安全**
   - 实现 CSRF Token
   - 对用户输入进行验证和过滤

4. **XSS 防护**
   - 对用户输入进行转义
   - 设置合适的 CSP 策略

---

## 联系与支持

如有问题，请查看：
- [Gin 文档](https://gin-gonic.com/docs/)
- [GORM 文档](https://gorm.io/docs/)
- [Go 官方文档](https://go.dev/doc/)
