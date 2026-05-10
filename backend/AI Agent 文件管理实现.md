# AI Agent 文件管理功能实现说明

## 概述

实现了 AI Agent 生成代码文件的自动保存和前端展示功能，支持目录结构展示、文件下载、流式响应等功能。

## 功能特性

### 后端功能

1. **文件模型** (`internal/models/file.go`)
   - `File` 结构体：存储文件信息（文件名、路径、内容、类型等）
   - `FileTree` 结构体：用于构建树形目录结构

2. **文件服务** (`internal/service/fileService.go`)
   - `CreateFile()`: 创建文件记录
   - `GetFilesBySession()`: 获取会话的所有文件
   - `GetFileByID()`: 根据 ID 获取文件
   - `DeleteFile()`: 删除文件
   - `BuildFileTree()`: 构建文件树（支持多级目录）
   - `SaveAgentFiles()`: 保存 Agent 生成的文件（自动分类到不同目录）

3. **文件 API** (`internal/handlers/chat.go`)
   - `GET /api/chat/sessions/:sessionId/files`: 获取文件列表（返回树形结构）
   - `GET /api/chat/files/:fileId`: 获取文件内容
   - `GET /api/chat/files/:fileId/download`: 下载文件
   - `POST /api/chat/send`: 发送消息（支持 SSE 流式响应）

4. **自动保存** (`internal/service/chatService.go`)
   - 修改 `ProcessMessage()` 函数
   - 新增 `callAgentSystemWithResults()` 函数
   - Agent 执行成功后自动保存文件到数据库
   - 新增 `ProcessMessageStream()` 函数支持流式处理
   - 新增 `callAgentSystemStream()` 函数支持 SSE 流式转发

### 前端功能

1. **状态管理** (`src/stores/chat.js`)
   - 新增 `fileTree` 状态
   - 新增 `setFileTree()` 方法

2. **文件树组件** (`src/views/Chat.vue`)
   - `FileTreeNode` 组件：递归展示文件树
   - 支持文件夹展开/折叠
   - 支持文件下载
   - 支持流式响应展示
   - 支持思考内容可收起/展开

3. **文件 API** (`src/api/chat.js`)
   - `getFiles()`: 获取文件列表
   - `downloadFile()`: 下载文件

4. **流式响应** (`src/views/Chat.vue`)
   - SSE 事件接收和处理
   - 思考步骤实时展示
   - 可收起/展开的思考区域
   - 流式内容渲染

## 文件目录结构

Agent 生成的文件会自动保存到以下目录结构：

```
code/                    # 代码文件
  ├── main.py           # 主要代码文件
  └── code_explanation.md  # 代码说明

analysis/               # 分析文件
  └── paper_analysis.md  # 论文解析

summary/                # 总结文件
  └── task_summary.md   # 任务总结
```

## 数据库表结构

### files 表

```sql
CREATE TABLE `files` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `session_id` int(11) NOT NULL COMMENT '会话 ID',
  `name` varchar(255) NOT NULL COMMENT '文件名',
  `path` varchar(512) NOT NULL COMMENT '文件路径（目录结构）',
  `content` text COMMENT '文件内容',
  `size` varchar(50) DEFAULT NULL COMMENT '文件大小（格式化后的字符串）',
  `type` varchar(50) DEFAULT NULL COMMENT '文件类型：code, paper, summary',
  `language` varchar(50) DEFAULT NULL COMMENT '编程语言（如果是代码）',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_session_id` (`session_id`),
  KEY `idx_type` (`type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

## 工作流程

### 1. Agent 执行并保存文件

```
用户发送请求
  ↓
后端判断需要调用 Agent
  ↓
调用 callAgentSystemWithResults()
  ↓
获取 Agent 返回的 results
  ↓
异步调用 SaveAgentFiles()
  ↓
根据文件类型保存到不同目录
  ↓
文件保存到数据库
```

### 2. 流式响应工作流程

```
用户发送请求
  ↓
前端使用 fetch + ReadableStream 建立 SSE 连接
  ↓
后端调用 ProcessMessageStream()
  ↓
后端调用 callAgentSystemStream() 连接 AI Agent
  ↓
AI Agent 执行 execute_task_stream() 生成事件流
  ↓
事件类型：
  - start: 任务开始
  - thinking: 思考阶段（显示 Agent 执行状态）
  - plan: 任务规划结果
  - task_complete: 单个任务完成
  - complete: 全部完成（包含最终内容）
  - error: 错误信息
  ↓
前端实时接收并展示思考步骤
  ↓
用户可收起/展开思考内容
  ↓
任务完成后显示最终结果
  ↓
自动刷新文件列表
```

### 3. 前端展示文件树

```
用户切换会话
  ↓
调用 loadFiles(sessionId)
  ↓
后端返回文件树结构
  ↓
前端更新 fileTree 状态
  ↓
FileTreeNode 组件递归渲染
  ↓
展示可折叠的目录结构
```

### 3. 文件下载

```
用户点击下载按钮
  ↓
前端调用 downloadFile(file)
  ↓
发送 GET 请求到 /api/chat/files/:fileId/download
  ↓
后端设置响应头
  ↓
浏览器下载文件
```

## 使用示例

### 示例 1：生成代码文件

**用户输入**：
```
用 Python 实现一个快速排序算法
```

**Agent 执行**：
1. Code Agent 生成代码
2. 保存到 `code/main.py`
3. 代码说明保存到 `code/code_explanation.md`

**前端展示**：
```
📁 code/
  ├── 📄 main.py [下载]
  └── 📄 code_explanation.md [下载]
```

### 示例 2：完整研究任务

**用户输入**：
```
研究大模型机器遗忘的最新方法，找到相关论文，解析核心算法，并实现示例代码
```

**Agent 执行**：
1. Search Agent 搜索文献 → 保存到 `analysis/papers.json`
2. RAG Agent 解析论文 → 保存到 `analysis/paper_analysis.md`
3. Code Agent 生成代码 → 保存到 `code/main.py`
4. 总结 → 保存到 `summary/task_summary.md`

**前端展示**：
```
📁 analysis/
  └── 📄 paper_analysis.md [下载]
📁 code/
  └── 📄 main.py [下载]
📁 summary/
  └──  task_summary.md [下载]
```

## 代码示例

### 后端：保存 Agent 文件

```go
// SaveAgentFiles 保存 Agent 生成的文件
func SaveAgentFiles(sessionID uint, agentResponse map[string]interface{}) error {
    // 保存代码文件
    if codeResult, ok := agentResponse["code_1"].(map[string]interface{}); ok {
        if code, ok := codeResult["code"].(string); ok {
            file := &models.File{
                SessionID: sessionID,
                Name:      "main.py",
                Path:      "code/main.py",
                Content:   code,
                Size:      formatFileSize(len(code)),
                Type:      "code",
                Language:  "python",
            }
            CreateFile(file)
        }
    }
    
    // 保存论文解析结果
    if ragResult, ok := agentResponse["rag_1"].(map[string]interface{}); ok {
        if content, ok := ragResult["content"].(string); ok {
            file := &models.File{
                SessionID: sessionID,
                Name:      "paper_analysis.md",
                Path:      "analysis/paper_analysis.md",
                Content:   content,
                Type:      "paper",
            }
            CreateFile(file)
        }
    }
    
    return nil
}
```

### 前端：文件树组件

```vue
const FileTreeNode = {
  name: 'FileTreeNode',
  props: {
    node: {
      type: Object,
      required: true
    }
  },
  emits: ['download'],
  setup(props, { emit }) {
    const expanded = ref(false)
    
    const toggleExpand = () => {
      if (props.node.type === 'folder') {
        expanded.value = !expanded.value
      }
    }
    
    const handleDownload = (file) => {
      emit('download', file)
    }
    
    return {
      expanded,
      toggleExpand,
      handleDownload
    }
  },
  template: `
    <div class="file-tree-node">
      <div 
        class="node-content" 
        :class="{ 'is-folder': node.type === 'folder', 'expanded': expanded }"
        @click="toggleExpand"
      >
        <el-icon :size="18" v-if="node.type === 'folder'">
          <Folder v-if="!expanded" />
          <FolderOpened v-else />
        </el-icon>
        <el-icon :size="18" v-else>
          <Document />
        </el-icon>
        <span class="node-name">{{ node.name }}</span>
        <el-icon :size="14" class="download-icon" v-if="node.type === 'file'" @click.stop="handleDownload(node.file)">
          <Download />
        </el-icon>
      </div>
      <div v-if="node.type === 'folder' && expanded && node.children" class="node-children">
        <file-tree-node
          v-for="child in node.children"
          :key="child.name"
          :node="child"
          @download="handleDownload"
        />
      </div>
    </div>
  `
}
```

## 数据库初始化

运行以下 SQL 创建文件表：

```bash
# 在 MySQL 中执行
mysql -u root -p auto_researcher < backend/internal/db/myFile.sql
```

或者手动执行 SQL 文件中的内容。

## 测试步骤

### 1. 初始化数据库

```bash
mysql -u root -p
use auto_researcher;
source backend/internal/db/myFile.sql;
```

### 2. 启动服务

```bash
# 启动后端
cd backend
go run main.go

# 启动前端
cd frontend
npm run dev
```

### 3. 测试文件生成

1. 登录系统
2. 创建新会话
3. 发送需要生成代码的请求
4. 查看右侧文件栏是否显示文件树
5. 点击文件夹展开/折叠
6. 点击下载按钮下载文件

## 注意事项

1. **数据库迁移**：需要先执行 SQL 创建 `files` 表
2. **异步保存**：文件保存是异步的，不会阻塞 AI 回复
3. **文件权限**：确保数据库用户有创建表的权限
4. **文件大小**：大文件可能需要调整 MySQL 的 `max_allowed_packet` 设置

## 后续优化

- [ ] 支持文件预览（代码高亮显示）
- [ ] 支持文件编辑
- [ ] 支持文件删除
- [ ] 支持文件重命名
- [ ] 支持批量下载（打包成 ZIP）
- [ ] 支持文件搜索
- [ ] 支持文件版本管理
- [ ] 支持更多文件类型（图片、PDF 等）
