# DeepSeek AI 集成完成！🎉

## ✅ 已完成的工作

### 1. 后端集成
- ✅ 实现 DeepSeek-v4-flash API 调用
- ✅ 添加请求/响应数据结构
- ✅ 错误处理和日志记录
- ✅ 环境变量配置

### 2. 配置文件
- ✅ 更新 `.env` 文件，添加 `DEEPSEEK_API_KEY` 配置项
- ✅ 创建 `AI 配置说明.md` 文档

### 3. 代码结构
```
backend/
├── internal/
│   └── service/
│       └── chatService.go          # ✅ AI 接口调用核心代码
├── .env                             # ✅ 环境变量配置
├── AI 配置说明.md                     # ✅ 详细配置文档
└── DeepSeek AI 集成完成.md           # ✅ 本文件
```

## 🚀 快速开始

### 步骤 1：获取 API Key
1. 访问 https://platform.deepseek.com/
2. 注册并登录
3. 在 [API Keys 页面](https://platform.deepseek.com/api_keys) 创建 API Key
4. 复制 API Key（格式：`sk-xxxxxxxx`）

### 步骤 2：配置环境变量
编辑 `backend/.env` 文件：
```env
DEEPSEEK_API_KEY=sk-your-actual-api-key-here
```

### 步骤 3：重启后端
```bash
# 停止当前运行的服务（Ctrl+C）
# 重新启动
cd backend
.\build.exe
```

### 步骤 4：测试对话
1. 打开前端：http://localhost:3001/
2. 登录账号
3. 点击"+ 新增会话"
4. 输入问题，例如：
   - "你好，请介绍一下你自己"
   - "今天天气怎么样？"
   - "帮我写一段 Python 代码，实现快速排序"

## 📊 API 调用流程

```
用户发送消息
  ↓
前端调用 /api/chat/send
  ↓
后端接收请求
  ↓
保存用户消息到数据库
  ↓
调用 DeepSeek API
  ↓
获取 AI 回复
  ↓
保存 AI 回复到数据库
  ↓
返回给前端
```

## 🔧 核心代码

### chatService.go - callDeepSeekAPI 函数

```go
func callDeepSeekAPI(userContent string) (string, error) {
    // 1. 从环境变量获取 API Key
    apiKey := os.Getenv("DEEPSEEK_API_KEY")
    
    // 2. 构建请求
    requestBody := DeepSeekRequest{
        Model: "deepseek-v4-flash",
        Messages: []DeepSeekMessage{
            {Role: "system", Content: "你是一个有帮助的 AI 助手。"},
            {Role: "user", Content: userContent},
        },
        Stream: false,
    }
    
    // 3. 发送 HTTP 请求
    req, _ := http.NewRequest("POST", 
        "https://api.deepseek.com/chat/completions", 
        bytes.NewBuffer(jsonData))
    req.Header.Set("Authorization", "Bearer "+apiKey)
    
    // 4. 获取响应
    resp, _ := client.Do(req)
    
    // 5. 解析并返回 AI 回复
    return response.Choices[0].Message.Content, nil
}
```

## 💡 示例对话

### 示例 1：日常对话
**用户**：你好，请介绍一下你自己  
**AI**：你好！我是 AutoResearcher 的 AI 助手，基于 DeepSeek-v4-flash 模型。我可以帮助你回答问题、编写代码、分析文档等。有什么我可以帮助你的吗？

### 示例 2：代码生成
**用户**：帮我写一个 Python 的快速排序  
**AI**：
```python
def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)

# 测试
arr = [3, 6, 8, 10, 1, 2, 1]
print(quick_sort(arr))
# 输出：[1, 1, 2, 3, 6, 8, 10]
```

### 示例 3：知识问答
**用户**：什么是机器学习？  
**AI**：机器学习是人工智能的一个分支，它使计算机能够从数据中学习并做出决策或预测，而无需被明确编程。机器学习算法通过训练数据建立模型，然后使用该模型进行预测或决策...

## 📈 性能指标

### DeepSeek-v4-flash
- **响应时间**：通常 < 2 秒
- **上下文窗口**：1M tokens
- **价格**：输入 ¥1/百万 tokens，输出 ¥2/百万 tokens
- **激活参数**：13B
- **总参数**：284B

### 成本估算
假设每次对话：
- 用户输入：100 tokens
- AI 回复：500 tokens
- 单次成本：约 ¥0.0011

**1000 次对话成本**：约 ¥1.1 元

## 🔍 调试技巧

### 查看后端日志
```bash
# 后端会输出详细的错误信息
# 如果 AI 调用失败，检查日志中的错误信息
```

### 常见错误
1. **未配置 DEEPSEEK_API_KEY**
   - 错误：`AI 接口调用失败：未配置 DEEPSEEK_API_KEY 环境变量`
   - 解决：检查 `.env` 文件并重启后端

2. **API Key 无效**
   - 错误：`API 返回错误状态码：401`
   - 解决：检查 API Key 是否正确

3. **网络超时**
   - 错误：`HTTP 请求失败：context deadline exceeded`
   - 解决：检查网络连接，可能需要 30 秒超时

## 📝 后续优化

### 近期计划
- [ ] 实现流式输出（SSE），提升用户体验
- [ ] 添加对话历史上下文，支持多轮对话
- [ ] AI 自动总结会话标题
- [ ] 添加请求重试机制

### 长期计划
- [ ] 支持多种 AI 模型切换
- [ ] 实现用户级别的配额管理
- [ ] 添加敏感词过滤
- [ ] 实现 AI 回复缓存

##  相关文档

- [AI 配置说明.md](./AI 配置说明.md) - 详细的配置和使用文档
- [DeepSeek API 官方文档](https://api-docs.deepseek.com/zh-cn/)
- [DeepSeek-v4 技术报告](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/blob/main/DeepSeek_V4.pdf)

## 🎉 开始使用

现在你可以：
1. 配置 API Key
2. 重启后端
3. 在前端与 AI 对话
4. 享受 DeepSeek-v4-flash 带来的智能体验！

祝你使用愉快！🚀
