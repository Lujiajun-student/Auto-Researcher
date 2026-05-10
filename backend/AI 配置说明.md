# DeepSeek AI 配置说明

## 1. 获取 API Key

### 步骤：
1. 访问 [DeepSeek 开放平台](https://platform.deepseek.com/)
2. 注册/登录账号
3. 进入 [API Keys 管理页面](https://platform.deepseek.com/api_keys)
4. 点击"创建 API Key"
5. 复制生成的 API Key（格式类似：`sk-xxxxxxxxxxxxxxxxxxxxxxxx`）

## 2. 配置环境变量

### 编辑 `.env` 文件

在 `backend/.env` 文件中添加：

```env
# DeepSeek AI API Key
DEEPSEEK_API_KEY=sk-your-actual-api-key-here
```

**注意**：将 `sk-your-actual-api-key-here` 替换为你实际的 API Key

## 3. 重启后端服务

配置完成后，需要重启后端服务使配置生效：

```bash
# Windows
# 停止当前运行的后端服务（Ctrl+C）
# 重新启动
cd backend
go run main.go

# 或者使用编译后的版本
.\build.exe
```

## 4. 测试 AI 功能

### 方法 1：通过前端测试
1. 打开前端页面（http://localhost:3001/）
2. 登录账号
3. 点击"+ 新建会话"
4. 在聊天框输入问题，例如："你好，请介绍一下你自己"
5. 查看 AI 回复

### 方法 2：通过 API 测试工具
```bash
POST http://localhost:8080/api/chat/send
Content-Type: application/json
Authorization: Bearer YOUR_JWT_TOKEN

{
  "session_id": 1,
  "content": "你好，请介绍一下你自己"
}
```

## 5. 模型说明

### DeepSeek-v4-flash

**特点**：
- 🚀 **快速响应**：13B 激活参数，推理速度快
- 💰 **经济实惠**：输入 ¥1/百万 tokens，输出 ¥2/百万 tokens
- 📚 **1M 上下文**：支持超长对话历史
- 🎯 **性能优秀**：推理能力接近 V4-Pro

**适用场景**：
- ✅ 日常对话
- ✅ 简单问答
- ✅ 文本生成
- ✅ 代码辅助
- ✅ 高并发场景

## 6. 常见问题

### Q1: 提示"未配置 DEEPSEEK_API_KEY 环境变量"
**解决**：检查 `.env` 文件是否正确配置，并重启后端服务

### Q2: API 调用失败
**解决**：
1. 检查 API Key 是否正确
2. 检查网络连接
3. 查看后端日志获取详细错误信息

### Q3: 响应速度慢
**解决**：
- DeepSeek-v4-flash 通常响应很快
- 如果慢，可能是网络问题或 API 限流
- 考虑检查 API 余额是否充足

### Q4: 如何查看 API 使用情况？
**解决**：访问 [DeepSeek 控制台](https://platform.deepseek.com/) 查看用量和余额

## 7. 费用说明

### DeepSeek-v4-flash 定价
- **输入**：¥1 元 / 百万 tokens
- **输出**：¥2 元 / 百万 tokens

### 估算示例
一次典型对话：
- 用户输入：100 tokens
- AI 回复：500 tokens
- 费用：100/1M × ¥1 + 500/1M × ¥2 = ¥0.0011

**结论**：非常经济实惠！

## 8. 安全提示

⚠️ **重要安全提醒**：

1. **不要泄露 API Key**
   - 不要提交到 Git 仓库
   - 不要分享给他人
   - 不要在前端代码中使用

2. **设置使用限额**
   - 在 DeepSeek 控制台设置每月预算上限
   - 定期监控使用情况

3. **生产环境建议**
   - 使用环境变量管理
   - 考虑添加请求频率限制
   - 实现用户级别的配额管理

## 9. 后续优化计划

- [ ] 支持流式输出（SSE）
- [ ] 实现对话历史上下文
- [ ] 添加 AI 自动总结会话标题
- [ ] 支持多种 AI 模型切换
- [ ] 实现用户配额管理

## 10. 参考资料

- [DeepSeek API 官方文档](https://api-docs.deepseek.com/zh-cn/)
- [DeepSeek-v4 技术报告](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/blob/main/DeepSeek_V4.pdf)
- [DeepSeek 开放平台](https://platform.deepseek.com/)
