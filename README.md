* # AutoResearcher —— 多智能体学术研究自动化系统

  ## 1. 项目描述 (Project Description)
  **AutoResearcher** 是一个面向 AI/ML 研究场景的 Multi-Agent 系统，具备自主规划研究任务、检索前沿论文、深度阅读理解以及生成和执行实验代码的能力。

  该系统特别适合处理前沿且复杂的学术命题（如大模型机器遗忘等领域），系统能够自动调度多个专业 Agent（搜索、RAG、代码执行），通过流式 API 返回研究进展，并在本地隔离的 Docker 沙箱环境中完成代码验证。

  ## 2. 系统整体架构与技术栈选型

  为了构建高吞吐的流式响应并保证后端的高并发处理能力，系统采用 **前后端分离 + AI微服务** 的架构。

  ### 🎨 前端技术栈 (Frontend)
  * **核心框架**：**Vue.js 3 + Vite**，提供极致的冷启动速度和流畅的组件化开发体验。
  * **状态管理 & 路由**：Pinia + Vue Router。
  * **UI 组件库**：Element Plus，用于构建复杂的科研控制台界面。
  * **通信与渲染**：支持 SSE (Server-Sent Events) 接收流式数据，配合 Markdown 渲染实时展示论文摘要与代码。
  * **部署环境**：**Nginx**，处理静态资源代理与反向路由。

  ### ⚙️ 后端 API 与网关层 (Backend API Layer - Go)
  * **核心框架**：**Go (Golang) + Gin**。利用 Go 的高性能路由和极低的内存占用处理高并发请求。
  * **流式响应处理**：利用 Go 原生的 **http.Flusher** 实现 SSE 流式下发，完美匹配大模型的 Token 输出节奏。
  * **异步任务处理**：利用 **Goroutines** 和 **Channels** 异步调度下游 Python AI 服务，保证主线程非阻塞。
  * **接口测试与管理**：使用 **Postman** 进行多端 API 联调与测试。
  * **系统职责**：负责用户鉴权 (JWT)、项目任务生命周期管理、调度 Python AI 服务以及维护任务状态机。

  ### AI 模型与多智能体层 (AI & Agent Layer)
  * **核心语言**：Python。
  * **多智能体编排**：**LangGraph**，构建显式状态机，支持 Plan-and-Execute 模式调度子任务。
  * **RAG 引擎**：LlamaIndex / LangChain 配合向量数据库。
  * **工具调用**：MCP (Model Context Protocol) 集成，将能力封装成 MCP Server。

  ### 数据存储与基础设施 (Data & Infra)
  * **数据库 & ORM**：PostgreSQL/MySQL + **GORM**，持久化存储研究任务与元数据。
  * **缓存与短期记忆**：**Redis**，用于高速存取对话上下文及任务执行状态。
  * **向量存储**：**ChromaDB**，用于长文本和 PDF 文档的 Embedding 检索。
  * **沙箱环境**：基于 **Docker** 的容器化代码执行沙箱，确保实验代码安全运行。
  * **版本控制**：**GitHub**，管理多语言代码仓库。

  ---

  ## 3. 核心模块拆解与功能实现 (Core Modules)

  | 模块名称               | 核心功能设计                                                 | 采用技术                       |
  | :--------------------- | :----------------------------------------------------------- | :----------------------------- |
  | **Orchestrator Agent** | 接收输入并拆解任务（如：先查文献，再解析方法）。分配任务给子 Agent 并监控状态。 | LangGraph (Plan-and-Execute)   |
  | **Search Agent**       | 定向搜索 arXiv、Semantic Scholar 等学术知识库，返回文献列表。 | Tool calling + arXiv API       |
  | **RAG Agent**          | 完成 PDF 论文解析、向量化入库，并针对技术细节进行深度语义检索。 | LlamaIndex + ChromaDB          |
  | **Code Agent**         | 根据提取的算法或数据结构（如二叉树重构、并行框架等），生成并运行 Python 代码。 | Docker 沙箱 + Function calling |
  | **Go API Backend**     | 处理前端请求，管理任务 ID，将 Python 服务的流式输出通过 SSE 格式推给前端。 | Go (Gin) + http.Flusher        |

  ---

  ## 4. 项目实现流程 (Implementation Flow)

  **第 1 周：搭建 RAG 基础底座**
  * 使用 LangChain + ChromaDB 实现 arXiv 论文的摄入流水线与基础 QA。

  **第 2 周：引入 Agent 机制与 Tool Use**
  * 使用 LangGraph 构建 Orchestrator + Search Agent 的通信逻辑。
  * 接入外部搜索工具作为 Agent 可调用的 Tool。

  **第 3 周：完善 Multi-Agent 编排与 Code Agent**
  * 实现 Plan-and-Execute 模式，并开发基于 Docker 的代码执行沙箱。

  **第 4 周：Go 后端开发与服务集成**
  * 使用 **Gin** 封装业务 API，利用 **Goroutine** 并发调度 Python 服务。
  * 实现 **SSE 接口**，将 AI 的思考过程实时同步至前端。
  * 接入 **Redis** 管理多轮对话状态。

  **第 5 周：前端联调与打磨**
  * 基于 Vue 3 开发控制台，录制 Demo 演示视频，编写部署指南。