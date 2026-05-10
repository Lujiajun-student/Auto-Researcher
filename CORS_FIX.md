# 跨域问题解决方案总结

## 问题诊断

### 原始问题
```
登录时接口测试没问题，但页面显示 network error
```

### 根本原因
前端代码中使用了绝对的 `baseURL: 'http://localhost:8080/api'`，导致：
1. 浏览器直接向后端地址 `http://localhost:8080` 发送请求
2. 由于前后端运行在不同端口（3000 vs 8080），触发浏览器的**同源策略**限制
3. 产生跨域错误（CORS Error）

---

## 已实施的解决方案

### ✅ 方案 1：Vite 开发服务器代理（推荐用于开发）

**修改内容**：
- 文件：`frontend/src/utils/request.js`
- 修改：`baseURL: 'http://localhost:8080/api'` → `baseURL: '/api'`

**工作原理**：
```
浏览器 → Vite 开发服务器 (3000) → Vite 代理 → 后端 (8080)
        ↓
    同源请求，无跨域问题
```

**配置位置**：`frontend/vite.config.js`
```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8080',
      changeOrigin: true
    }
  }
}
```

**优点**：
- ✅ 配置简单
- ✅ 支持热更新
- ✅ 无需额外软件
- ✅ 开发体验好

**使用方法**：
```bash
# 1. 启动后端（终端 1）
cd backend
go run main.go

# 2. 启动前端（终端 2）
cd frontend
npm run dev

# 3. 访问 http://localhost:3000
```

---

### ✅ 方案 2：Nginx 反向代理（推荐用于生产）

**配置文件**：
- `nginx.dev.conf` - 开发环境
- `nginx.prod.conf` - 生产环境
- `nginx.conf` - 通用配置

**工作原理**：
```
浏览器 → Nginx (80) → 前端静态文件 或 后端 API
        ↓
    统一入口，无跨域问题
```

**核心配置**：
```nginx
location /api/ {
    proxy_pass http://localhost:8080/api/;
    
    # 跨域头部
    add_header Access-Control-Allow-Origin * always;
    add_header Access-Control-Allow-Methods 'GET, POST, OPTIONS' always;
    add_header Access-Control-Allow-Headers 'Authorization,Content-Type' always;
}
```

**优点**：
- ✅ 高性能
- ✅ 支持负载均衡
- ✅ 静态资源优化
- ✅ 生产环境标准方案

**安装步骤**（Windows）：
1. 下载 Nginx：https://nginx.org/en/download.html
2. 解压到项目目录
3. 复制 `nginx.prod.conf` 到 `nginx/conf/nginx.conf`
4. 启动：`start nginx`

---

## 方案对比

| 特性 | Vite 代理 | Nginx 反向代理 |
|------|----------|---------------|
| **适用环境** | 开发 | 生产 |
| **配置复杂度** | 简单 | 中等 |
| **性能** | 一般 | 优秀 |
| **热更新** | ✅ 支持 | ❌ 不支持 |
| **静态资源优化** | ❌ 无 | ✅ Gzip/缓存 |
| **负载均衡** | ❌ 无 | ✅ 支持 |
| **HTTPS** | ❌ 需配置 | ✅ 原生支持 |

---

## 快速启动

### 方法 1：使用启动脚本（推荐）

**Windows CMD**：
```cmd
start-dev.bat
```

**PowerShell**：
```powershell
.\start-dev.ps1
```

### 方法 2：手动启动

```bash
# 终端 1 - 后端
cd backend
go run main.go

# 终端 2 - 前端
cd frontend
npm run dev
```

---

## 验证修复

### 1. 检查前端请求

打开浏览器开发者工具（F12）：

**Network 标签页**：
- 请求 URL 应该是 `/api/auth/login`（不是 `http://localhost:8080/api/auth/login`）
- 状态码应该是 200

### 2. 测试登录功能

1. 访问 http://localhost:3000
2. 点击"立即注册"创建账号
3. 输入用户名和密码
4. 点击登录
5. 应该成功跳转到聊天主页

### 3. 检查控制台

**不应该出现**：
- ❌ `Access to XMLHttpRequest at 'http://localhost:8080/...' from origin 'http://localhost:3000' has been blocked by CORS policy`
- ❌ `Network Error`

**可能出现**：
- ⚠️ `404 Not Found` - 后端接口未实现（正常，部分接口待开发）
- ℹ️ `Vue Router warn` - 路由守卫警告（已修复）

---

## 常见问题

### Q1: 端口被占用

**错误**：`bind: Only one usage of each socket address`

**解决**：
```bash
# 查看占用端口的进程
netstat -ano | findstr :8080

# 结束进程
taskkill /F /PID <进程 ID>
```

### Q2: 跨域错误仍然存在

**检查清单**：
- [ ] 前端 `baseURL` 是否已改为 `/api`
- [ ] Vite 代理配置是否正确
- [ ] 后端是否运行在 8080 端口
- [ ] 防火墙是否阻止连接
- [ ] 浏览器缓存是否清除

**解决步骤**：
1. 清除浏览器缓存（Ctrl+Shift+Delete）
2. 重启前端开发服务器
3. 检查 `vite.config.js` 配置
4. 检查 `request.js` 的 `baseURL`

### Q3: 404 错误

**可能原因**：
- 后端接口未实现
- 路由配置错误
- 请求路径错误

**解决**：
```bash
# 检查后端日志
# 查看请求是否到达后端

# 使用 Postman 测试接口
POST http://localhost:8080/api/auth/login
Content-Type: application/json

{
  "username": "test",
  "password": "123456"
}
```

### Q4: Nginx 启动失败

**检查配置**：
```bash
cd nginx
nginx -t
```

**查看错误日志**：
```
logs/error.log
```

**常见错误**：
- 配置文件路径错误
- 端口被占用
- 权限问题

---

## 后端接口状态

### ✅ 已实现

- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/logout` - 退出登录
- `GET /api/auth/:userId` - 获取用户信息
- `DELETE /api/auth/:userId` - 删除用户

### ⏳ 待实现

- `GET /api/chat/sessions` - 获取会话列表
- `POST /api/chat/sessions` - 创建会话
- `DELETE /api/chat/sessions/:id` - 删除会话
- `GET /api/chat/sessions/:id/messages` - 获取消息
- `POST /api/chat/send` - 发送消息
- `GET /api/chat/sessions/:id/files` - 获取文件列表
- `GET /api/chat/files/:id` - 下载文件

详细接口文档见：`frontend/README.md`

---

## 总结

### ✅ 问题已解决

1. **前端代码修复**：`baseURL` 改为 `/api`
2. **Vite 代理配置**：已验证可用
3. **Nginx 配置**：提供生产环境方案
4. **启动脚本**：简化开发流程

### 📋 下一步

1. **开发环境**：直接使用 `npm run dev` 或启动脚本
2. **后端开发**：实现聊天相关接口
3. **生产部署**：使用 Nginx 部署

### 📚 相关文档

- `NGINX_SETUP.md` - Nginx 详细配置指南
- `frontend/README.md` - 前端 API 接口文档
- `frontend/QUICKSTART.md` - 前端快速启动
- `start-dev.bat` / `start-dev.ps1` - 开发环境启动脚本

---

**修复时间**：2026-05-09  
**修复状态**：✅ 已完成  
**测试状态**：✅ 跨域问题已解决
