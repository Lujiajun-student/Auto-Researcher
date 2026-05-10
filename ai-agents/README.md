# AI Agents - 多智能体学术研究自动化系统

## 📋 目录

- [概述](#概述)
- [架构设计](#架构设计)
- [Agent 介绍](#agent-介绍)
- [快速开始](#快速开始)
- [API 接口](#api-接口)
- [使用示例](#使用示例)
- [配置说明](#配置说明)

---

## 概述

基于 LangGraph 的多智能体系统，能够自主规划研究任务、检索前沿论文、深度阅读理解以及生成和执行实验代码。

### 核心能力

- 🎯 **任务规划**：自动拆解复杂研究任务为子任务
- 🔍 **文献搜索**：从 arXiv 等学术数据库搜索相关论文
- 📚 **论文解析**：深度解析论文方法和技术细节
- 💻 **代码实现**：根据论文方法生成可运行代码
- 🛡️ **沙箱执行**：在 Docker 容器中安全运行代码

---

## 架构设计

### 系统架构图

```
┌─────────────────────────────────────────────────┐
│              User Task Input                     │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│          Orchestrator Agent                      │
│  - 接收任务                                      │
│  - 拆解为子任务                                  │
│  - 分配给专门 Agent                              │
│  - 监控执行状态                                  │
└────────┬────────────────────────────────────────┘
         │
         ├─────────────┬──────────────┬──────────┐
         ▼             ▼              ▼          ▼
┌─────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Search      │ │  RAG     │ │  Code    │ │  ...     │
│ Agent       │ │  Agent   │ │  Agent   │ │  Agent   │
│ 搜索文献    │ │ 解析论文 │ │ 编写代码 │ │ 扩展     │
└─────────────┘ └──────────┘ └──────────┘ └──────────┘
         │             │              │
         └─────────────┴──────────────┘
                       │
                       ▼
         ┌─────────────────────────┐
         │   Results Aggregation   │
         │   结果汇总和总结        │
         └─────────────────────────┘
```

### 技术栈

- **编排框架**: LangGraph (Plan-and-Execute 模式)
- **LLM**: DeepSeek-v4-flash (支持 OpenAI 兼容 API)
- **搜索**: arXiv API
- **RAG**: LangChain + PyPDF2
- **代码执行**: Docker 沙箱
- **API**: FastAPI

---

## Agent 介绍

### 1. Orchestrator Agent（协调者）

**职责**：
- 接收复杂的学术研究任务
- 将任务拆解为多个子任务
- 分配给专门的 Agent 执行
- 监控执行进度

**能力**：
- 智能任务规划
- Agent 路由选择
- 状态监控

### 2. Search Agent（搜索专家）

**职责**：
- 从 arXiv 等学术数据库搜索论文
- 提取论文关键信息
- 整理搜索结果

**能力**：
- arXiv API 集成
- 相关性排序
- 结果总结

### 3. RAG Agent（论文解析专家）

**职责**：
- 下载并解析 PDF 论文
- 提取核心方法和技术细节
- 总结论文贡献

**能力**：
- PDF 解析
- 方法提取
- 技术总结

### 4. Code Agent（代码实现专家）

**职责**：
- 根据论文方法实现代码
- 提供完整可运行的示例
- 在沙箱中执行代码

**能力**：
- 代码生成
- 代码解释
- 调试修复
- 沙箱执行

---

## 快速开始

### 1. 安装依赖

```bash
cd ai-agents
pip install -r requirements.txt
```

### 2. 配置环境变量

编辑 `.env` 文件：

```env
# DeepSeek AI API 配置
DEEPSEEK_API_KEY=sk-your-api-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
```

### 3. 启动服务

```bash
# 方式 1：直接运行
python app.py

# 方式 2：使用 uvicorn
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 测试任务

```bash
curl -X POST http://localhost:8000/api/v1/task/execute \
  -H "Content-Type: application/json" \
  -d '{
    "description": "研究大模型机器遗忘的最新方法，找到相关论文，解析核心算法，并实现示例代码"
  }'
```

---

## API 接口

### 执行任务

**POST** `/api/v1/task/execute`

**请求体**：
```json
{
  "task_id": "可选的任务 ID",
  "description": "任务描述"
}
```

**响应**：
```json
{
  "task_id": "task_001",
  "status": "completed",
  "results": {
    "sub_tasks": [...],
    "summary": "任务总结"
  },
  "error": null
}
```

### 获取状态

**GET** `/api/v1/status`

**响应**：
```json
{
  "status": "running",
  "agents": {
    "orchestrator": {...},
    "search": {...},
    "rag": {...},
    "code": {...}
  }
}
```

### 健康检查

**GET** `/api/v1/health`

**响应**：
```json
{
  "status": "healthy"
}
```

---

## 使用示例

### 示例 1：研究任务

```python
from main import MultiAgentSystem
import asyncio

async def main():
    # 创建系统
    agent_system = MultiAgentSystem()
    
    # 执行任务
    result = await agent_system.execute_task(
        task_id="task_001",
        task_description="研究大模型机器遗忘的最新方法"
    )
    
    print(result)

asyncio.run(main())
```

### 示例 2：单独使用 Search Agent

```python
from agents.search import SearchAgent

agent = SearchAgent()
result = agent.search("machine unlearning in large language models")

print(f"找到 {result['count']} 篇论文")
print(f"总结：{result['summary']}")
```

### 示例 3：单独使用 Code Agent

```python
from agents.code import CodeAgent

agent = CodeAgent()
result = agent.generate_code("实现快速排序算法")

print(f"生成的代码:\n{result['code']}")
```

---

## 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | 必需 |
| `DEEPSEEK_BASE_URL` | DeepSeek API 基础 URL | https://api.deepseek.com |
| `DEEPSEEK_MODEL` | 使用的模型 | deepseek-v4-flash |

### Docker 配置

Code Agent 使用 Docker 沙箱执行代码，需要确保：

1. Docker 已安装并运行
2. 用户有权限访问 Docker socket
3. 网络配置允许拉取镜像

---

## 工作流示例

### 完整任务执行流程

```
1. 用户输入：研究大模型机器遗忘的最新方法

2. Orchestrator 拆解任务：
   - Search Agent: 搜索 arXiv 上关于机器遗忘的论文
   - RAG Agent: 解析找到的核心论文
   - Code Agent: 实现机器遗忘算法示例

3. Search Agent 执行：
   - 调用 arXiv API
   - 找到 10 篇相关论文
   - 返回论文列表和总结

4. RAG Agent 执行：
   - 下载 Top 3 论文的 PDF
   - 解析核心方法
   - 提取技术细节

5. Code Agent 执行：
   - 根据论文方法编写代码
   - 在 Docker 沙箱中测试
   - 返回可运行的示例

6. Orchestrator 汇总：
   - 收集所有 Agent 的结果
   - 生成完整报告
   - 返回给用户
```

---

## 后续扩展

### 计划添加的 Agent

- **Review Agent**: 评估论文质量和可信度
- **Experiment Agent**: 设计和运行对比实验
- **Writing Agent**: 撰写研究报告和论文
- **Visualization Agent**: 生成图表和可视化结果

### 功能增强

- [ ] 支持更多学术数据库（Semantic Scholar, Google Scholar）
- [ ] 添加向量数据库用于长期记忆
- [ ] 实现多轮对话和迭代优化
- [ ] 添加任务进度实时推送（SSE）
- [ ] 支持分布式任务执行

---

## 参考资料

- [LangGraph 官方文档](https://langchain-ai.github.io/langgraph/)
- [DeepSeek API 文档](https://api-docs.deepseek.com/)
- [arXiv API 文档](https://arxiv.org/help/api)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)

---

## 许可证

MIT License
