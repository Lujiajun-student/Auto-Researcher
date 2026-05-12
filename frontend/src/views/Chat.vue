<template>
  <div class="chat-container">
    <!-- 左侧会话列表 -->
    <div class="sidebar" :class="{ 'collapsed': leftSidebarCollapsed }">
      <div class="sidebar-header">
        <el-button @click="toggleLeftSidebar" text>
          <el-icon><Fold /></el-icon>
        </el-button>
        <span v-if="!leftSidebarCollapsed" class="title">会话列表</span>
        <el-button v-if="!leftSidebarCollapsed" @click="createNewSession" type="primary" size="small">
          <el-icon><Plus /></el-icon>
          新建会话
        </el-button>
      </div>
      
      <div class="session-list" v-if="!leftSidebarCollapsed">
        <div
          v-for="session in chatStore.sessions"
          :key="session.id"
          class="session-item"
          :class="{ active: chatStore.currentSessionId === session.id }"
          @click="openSessionTab(session)"
        >
          <el-icon><ChatDotRound /></el-icon>
          <span class="session-title">{{ session.title }}</span>
          <el-button
            class="delete-btn"
            @click.stop="deleteSession(session.id)"
            type="danger"
            size="small"
            text
          >
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
      </div>
    </div>

    <!-- 中间聊天区域 -->
    <div class="chat-main">
      <!-- 标签页栏 -->
      <div class="tabs-bar">
        <div
          v-for="tab in tabs"
          :key="tab.id"
          class="tab-item"
          :class="{ active: activeTabId === tab.id }"
          @click="switchTab(tab.id)"
        >
          <el-icon v-if="tab.type === 'session'"><ChatDotRound /></el-icon>
          <el-icon v-else><Document /></el-icon>
          <span class="tab-title">{{ tab.title }}</span>
          <el-icon class="tab-close" @click.stop="closeTab(tab.id)">
            <Close />
          </el-icon>
        </div>
        <div class="tabs-bar-actions">
          <el-button @click="handleLogout" text>
            <el-icon><SwitchButton /></el-icon>
            退出
          </el-button>
        </div>
      </div>

      <!-- 聊天内容区域 -->
      <div v-if="activeTab && activeTab.type === 'session'" class="chat-content">
        <div class="chat-header">
          <el-button @click="toggleLeftSidebar" text>
            <el-icon><Expand /></el-icon>
          </el-button>
          <span class="chat-title">{{ activeTab.title }}</span>
          <div class="header-actions">
            <el-button @click="toggleRightSidebar" text>
              <el-icon><Files /></el-icon>
            </el-button>
          </div>
        </div>
        
        <div class="messages-container" ref="messagesContainer">
          <div v-if="chatStore.messages.length === 0" class="empty-state">
            <el-empty description="开始新的对话吧" />
          </div>
          
          <div v-else class="messages-list">
            <div
              v-for="(message, index) in chatStore.messages"
              :key="index"
              class="message"
              :class="message.role"
            >
              <div class="message-avatar">
                <el-avatar v-if="message.role === 'user'" :size="40">
                  <el-icon><User /></el-icon>
                </el-avatar>
                <el-avatar v-else :size="40" style="background: #667eea">
                  <el-icon><Monitor /></el-icon>
                </el-avatar>
              </div>
              
              <div class="message-content">
                <div class="message-header">
                  <span class="message-role">{{ message.role === 'user' ? '你' : 'AI' }}</span>
                  <span class="message-time">{{ message.time || getCurrentTime() }}</span>
                </div>
                <div class="message-text" v-html="renderMarkdown(message.content)"></div>
              </div>
            </div>
            
            <div v-if="isThinking" class="message ai thinking">
              <div class="message-avatar">
                <el-avatar :size="40" style="background: #667eea">
                  <el-icon><Monitor /></el-icon>
                </el-avatar>
              </div>
              <div class="message-content">
                <!-- 思考内容区域 -->
                <div class="thinking-section">
                  <div class="thinking-header" @click="thinkingExpanded = !thinkingExpanded">
                    <el-icon class="loading"><Loading /></el-icon>
                    <span class="thinking-title">AI 正在思考中...</span>
                    <el-icon class="expand-icon" :class="{ expanded: thinkingExpanded }">
                      <ArrowDown />
                    </el-icon>
                  </div>
                  <div v-show="thinkingExpanded" class="thinking-content">
                    <div v-for="(step, index) in thinkingSteps" :key="index" class="thinking-step">
                      <span class="step-agent">{{ step.agent }}</span>
                      <span class="step-message">{{ step.message }}</span>
                    </div>
                  </div>
                </div>
                <!-- 流式内容区域 -->
                <div v-if="streamingContent" class="streaming-content" v-html="renderMarkdown(streamingContent)"></div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="input-area">
          <el-input
            v-model="inputMessage"
            type="textarea"
            :rows="3"
            placeholder="输入你的问题，支持 Markdown 格式..."
            @keydown.ctrl.enter="sendMessage"
            resize="none"
          />
          <div class="input-actions">
            <el-button type="primary" @click="sendMessage" :loading="isThinking" :disabled="!inputMessage.trim()">
              <el-icon><Promotion /></el-icon>
              发送 (Ctrl+Enter)
            </el-button>
          </div>
        </div>
      </div>

      <!-- 文件内容区域 -->
      <div v-else-if="activeTab && activeTab.type === 'file'" class="file-content">
        <div class="file-header">
          <el-icon><Document /></el-icon>
          <span class="file-title">{{ activeTab.title }}</span>
          <div class="file-actions">
            <el-button @click="downloadFile(activeTab.file)" type="primary" size="small">
              <el-icon><Download /></el-icon>
              下载
            </el-button>
          </div>
        </div>
        <div class="file-body">
          <pre class="file-text">{{ activeTab.content || '加载中...' }}</pre>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="empty-main">
        <el-empty description="选择一个会话或文件开始" :image-size="200" />
      </div>
    </div>

    <!-- 右侧文件栏 -->
    <div class="right-sidebar" :class="{ 'collapsed': rightSidebarCollapsed }">
      <!-- 收起状态下的展开按钮 -->
      <div v-if="rightSidebarCollapsed" class="expand-button" @click="toggleRightSidebar">
        <el-icon><Expand /></el-icon>
      </div>
      
      <!-- 展开状态下的完整内容 -->
      <template v-else>
        <div class="sidebar-header">
          <span class="title">AI 生成的文件</span>
          <div class="header-actions">
            <el-button @click="loadFiles(chatStore.currentSessionId)" text title="刷新文件列表">
              <el-icon><Refresh /></el-icon>
            </el-button>
            <el-button @click="toggleRightSidebar" text>
              <el-icon><Fold /></el-icon>
            </el-button>
          </div>
        </div>
        
        <div class="file-list">
          <div v-if="chatStore.fileTree.length > 0">
            <file-tree-node
              v-for="node in chatStore.fileTree"
              :key="node.name"
              :node="node"
              @download="downloadFile"
              @open="openFileTab"
            />
          </div>
          <el-empty v-else description="暂无生成的文件" :image-size="80" />
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch, h } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { useChatStore } from '@/stores/chat'
import { getSessions, createSession, deleteSession as deleteSessionApi, getMessages, sendMessage as sendChatMessage, getFiles } from '@/api/chat'
import { logout } from '@/api/auth'
import markdownIt from 'markdown-it'
import { 
  Fold, Plus, ChatDotRound, Delete, Expand, Files, SwitchButton, 
  User, Monitor, Loading, Promotion, Document, Folder, FolderOpened, 
  Download, Refresh, ChatRound, Close, ArrowDown 
} from '@element-plus/icons-vue'
import { readSSEStream } from '@/utils/sse'

const router = useRouter()
const userStore = useUserStore()
const chatStore = useChatStore()

const leftSidebarCollapsed = ref(false)
const rightSidebarCollapsed = ref(false)
const inputMessage = ref('')
const isThinking = ref(false)
const messagesContainer = ref(null)
const refreshTimer = ref(null)

// 标签页系统
const tabs = ref([])
const activeTabId = ref(null)
let tabIdCounter = 0

const activeTab = computed(() => {
  return tabs.value.find(tab => tab.id === activeTabId.value)
})

// 流式响应相关
const streamingContent = ref('')
const thinkingSteps = ref([])
const thinkingExpanded = ref(true)

const md = markdownIt()

// 文件树组件
const FileTreeNode = {
  name: 'FileTreeNode',
  props: {
    node: {
      type: Object,
      required: true
    },
    level: {
      type: Number,
      default: 0
    }
  },
  emits: ['download', 'open'],
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
    
    const handleOpen = (file) => {
      emit('open', file)
    }
    
    return {
      expanded,
      toggleExpand,
      handleDownload,
      handleOpen
    }
  },
  render() {
    const node = this.node
    const isFolder = node.type === 'folder'
    const level = this.level || 0
    
    const children = isFolder && this.expanded && node.children
      ? node.children.map(child => h(FileTreeNode, {
          key: child.name,
          node: child,
          level: level + 1,
          onDownload: this.handleDownload,
          onOpen: this.handleOpen
        }))
      : []
    
    return h('div', { class: 'file-tree-node' }, [
      h('div', {
        class: {
          'node-content': true,
          'is-folder': isFolder,
          'expanded': this.expanded
        },
        style: { paddingLeft: (level * 16 + 8) + 'px' },
        onClick: () => {
          if (!isFolder && node.file) {
            this.handleOpen(node.file)
          } else {
            this.toggleExpand()
          }
        }
      }, [
        isFolder ? h('span', { 
          class: { 'expand-arrow': true, 'expanded': this.expanded },
          style: { marginRight: '4px', display: 'inline-block', width: '12px', textAlign: 'center' }
        }, this.expanded ? '▼' : '▶') : h('span', { style: { width: '12px', display: 'inline-block' } }),
        h('span', { class: 'node-name' }, node.name),
        !isFolder ? h('el-icon', {
          size: 14,
          class: 'download-icon',
          onClick: (e) => {
            e.stopPropagation()
            this.handleDownload(node.file)
          }
        }, () => h(Download)) : null
      ]),
      isFolder && this.expanded && node.children
        ? h('div', { class: 'node-children' }, children)
        : null
    ])
  }
}

const currentSessionTitle = computed(() => {
  const session = chatStore.sessions.find(s => s.id === chatStore.currentSessionId)
  return session ? session.title : '新对话'
})

const toggleLeftSidebar = () => {
  leftSidebarCollapsed.value = !leftSidebarCollapsed.value
}

const toggleRightSidebar = () => {
  rightSidebarCollapsed.value = !rightSidebarCollapsed.value
}

const getCurrentTime = () => {
  const now = new Date()
  return now.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const renderMarkdown = (content) => {
  return md.render(content)
}

const loadSessions = async () => {
  try {
    const res = await getSessions()
    chatStore.setSessions(res.data || [])
  } catch (error) {
    console.error('加载会话失败:', error)
  }
}

const createNewSession = async () => {
  try {
    // 使用默认标题"新增会话"，后续计划由 AI 自动总结生成标题
    const res = await createSession('新增会话')
    chatStore.addSession(res.data)
    // 创建成功后自动选中新会话
    openSessionTab(res.data)
    ElMessage.success('创建成功')
  } catch (error) {
    console.error('创建会话失败:', error)
    ElMessage.error('创建失败，请重试')
  }
}

// 打开会话标签页
const openSessionTab = async (session) => {
  // 检查是否已存在该会话的标签页
  const existingTab = tabs.value.find(tab => tab.type === 'session' && tab.sessionId === session.id)
  if (existingTab) {
    switchTab(existingTab.id)
    return
  }
  
  // 创建新标签页
  const tabId = ++tabIdCounter
  tabs.value.push({
    id: tabId,
    type: 'session',
    sessionId: session.id,
    title: session.title
  })
  
  switchTab(tabId)
}

// 打开文件标签页
const openFileTab = async (file) => {
  // 检查是否已存在该文件的标签页
  const existingTab = tabs.value.find(tab => tab.type === 'file' && tab.fileId === file.id)
  if (existingTab) {
    switchTab(existingTab.id)
    return
  }
  
  // 创建新标签页
  const tabId = ++tabIdCounter
  tabs.value.push({
    id: tabId,
    type: 'file',
    fileId: file.id,
    title: file.name,
    file: file,
    content: ''
  })
  
  switchTab(tabId)
  
  // 加载文件内容
  try {
    const response = await fetch(`/api/chat/files/${file.id}`, {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    if (!response.ok) {
      throw new Error('加载文件失败')
    }
    const result = await response.json()
    const tab = tabs.value.find(t => t.id === tabId)
    if (tab) {
      tab.content = result.data.content || ''
    }
  } catch (error) {
    console.error('加载文件内容失败:', error)
    const tab = tabs.value.find(t => t.id === tabId)
    if (tab) {
      tab.content = '加载失败，请稍后重试'
    }
  }
}

// 切换标签页
const switchTab = async (tabId) => {
  activeTabId.value = tabId
  const tab = tabs.value.find(t => t.id === tabId)
  
  if (tab && tab.type === 'session') {
    // 加载会话消息
    chatStore.setCurrentSession(tab.sessionId)
    try {
      const res = await getMessages(tab.sessionId)
      chatStore.setMessages(res.data || [])
      // 加载文件列表
      await loadFiles(tab.sessionId)
      await nextTick()
      scrollToBottom()
    } catch (error) {
      chatStore.setMessages([])
      chatStore.setFileTree([])
      console.error('加载会话失败:', error)
    }
  }
}

// 关闭标签页
const closeTab = (tabId) => {
  const index = tabs.value.findIndex(tab => tab.id === tabId)
  if (index === -1) return
  
  tabs.value.splice(index, 1)
  
  // 如果关闭的是当前标签页，切换到相邻标签页
  if (activeTabId.value === tabId) {
    if (tabs.value.length > 0) {
      const newIndex = Math.min(index, tabs.value.length - 1)
      switchTab(tabs.value[newIndex].id)
    } else {
      activeTabId.value = null
      chatStore.clearCurrentChat()
    }
  }
}

const deleteSession = async (sessionId) => {
  try {
    await deleteSessionApi(sessionId)
    chatStore.setSessions(chatStore.sessions.filter(s => s.id !== sessionId))
    if (chatStore.currentSessionId === sessionId) {
      chatStore.clearCurrentChat()
    }
    ElMessage.success('删除成功')
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

const sendMessage = async () => {
  if (!inputMessage.value.trim() || isThinking.value) return
  
  const userMessage = {
    role: 'user',
    content: inputMessage.value,
    time: getCurrentTime()
  }
  
  chatStore.addMessage(userMessage)
  const userContent = inputMessage.value
  inputMessage.value = ''
  isThinking.value = true
  streamingContent.value = ''
  thinkingSteps.value = []
  thinkingExpanded.value = true
  
  await nextTick()
  scrollToBottom()
  
  try {
    // 使用 SSE 流式接口
    const response = await fetch('/api/chat/send', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${userStore.token}`
      },
      body: JSON.stringify({
        session_id: chatStore.currentSessionId,
        content: userContent
      })
    })
    
    // 使用 SSE 工具类读取流
    let completeData = null
    
    await readSSEStream(response, {
      onEvent: (event) => {
        console.log('[SSE] 收到事件:', event.type, event.data)
        handleStreamEvent(event)
        
        // 保存完整数据
        if (event.type === 'complete' && event.data) {
          completeData = event.data
        }
      },
      onError: (error) => {
        console.error('[SSE] 错误:', error)
      },
      onComplete: () => {
        console.log('[SSE] 流读取完成')
      },
      debug: true
    })
    
    // 处理完成后
    if (completeData) {
      // 优先使用 content 字段（后端增强后的），如果没有再用 summary
      const finalContent = completeData.content || completeData.summary || ''
      
      const aiMessage = {
        role: 'assistant',
        content: finalContent,
        time: getCurrentTime()
      }
      chatStore.addMessage(aiMessage)
      
      // 发送成功后自动刷新文件列表
      await loadFiles(chatStore.currentSessionId)
      
      ElMessage.success('发送成功')
    }
  } catch (error) {
    console.error('[SSE] 发送消息失败:', error)
    ElMessage.error(`发送失败：${error.message}`)
  } finally {
    isThinking.value = false
    streamingContent.value = ''
    thinkingSteps.value = []
    await nextTick()
    scrollToBottom()
  }
}

// 处理流式事件
const handleStreamEvent = (event) => {
  const { type, data } = event
  
  if (!type) {
    console.warn('[SSE] 收到未知类型事件:', event)
    return
  }
  
  console.log('[SSE] 处理事件:', type, data)
  
  switch (type) {
    case 'start':
      // 任务开始
      console.log('[SSE] 任务开始')
      break
    
    case 'thinking':
      // 思考阶段
      if (data && data.agent && data.message) {
        thinkingSteps.value.push({
          agent: getAgentName(data.agent),
          message: data.message,
          timestamp: Date.now()
        })
      }
      break
    
    case 'plan':
      // 任务规划
      if (data && data.sub_tasks) {
        thinkingSteps.value.push({
          agent: '规划',
          message: `拆解为 ${data.count || data.sub_tasks.length} 个子任务`,
          subTasks: data.sub_tasks,
          timestamp: Date.now()
        })
      }
      break
    
    case 'task_complete':
      // 任务完成
      if (data && data.agent) {
        thinkingSteps.value.push({
          agent: getAgentName(data.agent),
          message: '任务完成',
          timestamp: Date.now()
        })
      }
      break
    
    case 'complete':
      // 全部完成
      if (data) {
        const content = data.content || data.summary || ''
        streamingContent.value = content
        console.log('[SSE] 完成，内容长度:', content.length)
      }
      break
    
    case 'error':
      // 错误
      if (data && data.error) {
        streamingContent.value = `❌ 执行失败：${data.error}`
        ElMessage.error(`执行失败：${data.error}`)
      }
      break
    
    default:
      console.warn('[SSE] 未处理的事件类型:', type)
  }
}

// 获取 Agent 显示名称
const getAgentName = (agentType) => {
  const names = {
    'orchestrator': ' 协调者',
    'search': ' 搜索',
    'rag': ' 解析',
    'code': ' 代码'
  }
  return names[agentType] || agentType
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const loadFiles = async (sessionId) => {
  try {
    const res = await getFiles(sessionId)
    chatStore.setFileTree(res.data || [])
  } catch (error) {
    console.error('加载文件列表失败:', error)
    chatStore.setFileTree([])
  }
}

const downloadFile = async (file) => {
  if (!file || !file.id) {
    ElMessage.error('文件信息无效')
    return
  }
  try {
    const response = await fetch(`/api/chat/files/${file.id}/download`, {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    if (!response.ok) {
      throw new Error('下载失败')
    }
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = file.name
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
    ElMessage.success('下载成功')
  } catch (error) {
    console.error('下载文件失败:', error)
    ElMessage.error('下载失败')
  }
}

const handleLogout = async () => {
  try {
    await logout()
  } catch (error) {
    console.error('退出失败:', error)
  }
  userStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}

onMounted(() => {
  loadSessions()
})

onUnmounted(() => {
  // 清理定时器
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
    refreshTimer.value = null
  }
})
</script>

<style scoped>
.chat-container {
  display: flex;
  height: 100vh;
  background: #f5f7fa;
}

.sidebar {
  width: 280px;
  background: #fff;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  transition: width 0.3s;
}

.sidebar.collapsed {
  width: 60px;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  gap: 8px;
}

.sidebar-header .header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.sidebar-header .title {
  flex: 1;
  font-weight: bold;
  font-size: 16px;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.session-item {
  display: flex;
  align-items: center;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 8px;
  transition: background 0.2s;
}

.session-item:hover {
  background: #f5f7fa;
}

.session-item.active {
  background: #e6f7ff;
  color: #1890ff;
}

.session-item .session-title {
  flex: 1;
  margin-left: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-item .delete-btn {
  opacity: 0;
  transition: opacity 0.2s;
}

.session-item:hover .delete-btn {
  opacity: 1;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
  overflow: hidden;
}

/* 标签页栏样式 */
.tabs-bar {
  display: flex;
  align-items: center;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
  overflow-x: auto;
  min-height: 40px;
  padding: 4px 8px 0;
}

.tabs-bar-actions {
  margin-left: auto;
  padding-right: 8px;
}

.tabs-bar::-webkit-scrollbar {
  height: 4px;
}

.tabs-bar::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 2px;
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 6px 6px 0 0;
  cursor: pointer;
  font-size: 13px;
  color: #606266;
  background: #e4e7ed;
  margin-right: 4px;
  transition: background 0.2s;
  white-space: nowrap;
  max-width: 200px;
}

.tab-item:hover {
  background: #dcdfe6;
}

.tab-item.active {
  background: #fff;
  color: #409EFF;
  font-weight: 500;
}

.tab-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tab-close {
  font-size: 12px;
  opacity: 0;
  transition: opacity 0.2s;
}

.tab-item:hover .tab-close {
  opacity: 1;
}

.tab-close:hover {
  color: #f56c6c;
}

/* 聊天内容区域 */
.chat-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 文件内容区域 */
.file-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.file-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 24px;
  border-bottom: 1px solid #e4e7ed;
  background: #fafafa;
}

.file-title {
  flex: 1;
  font-weight: bold;
  font-size: 16px;
}

.file-actions {
  display: flex;
  gap: 8px;
}

.file-body {
  flex: 1;
  overflow: auto;
  padding: 24px;
  background: #fff;
}

.file-text {
  margin: 0;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
  color: #303133;
}

/* 空状态 */
.empty-main {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
}

.chat-header {
  padding: 16px 24px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  gap: 12px;
}

.chat-title {
  flex: 1;
  font-weight: bold;
  font-size: 18px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.empty-state {
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.message {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.message.user {
  flex-direction: row-reverse;
}

.message-content {
  max-width: 70%;
}

.message-header {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 8px;
  font-size: 14px;
  color: #909399;
}

.message.user .message-header {
  flex-direction: row-reverse;
}

.message-role {
  font-weight: bold;
}

.message-text {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 8px;
  line-height: 1.6;
}

.message.user .message-text {
  background: #e6f7ff;
}

.message-text :deep(p) {
  margin: 0 0 8px 0;
}

.message-text :deep(p:last-child) {
  margin: 0;
}

.message-text :deep(pre) {
  background: #282c34;
  color: #abb2bf;
  padding: 16px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 8px 0;
}

.message-text :deep(code) {
  font-family: 'Consolas', 'Monaco', monospace;
}

.thinking-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #909399;
}

/* 思考内容区域样式 */
.thinking-section {
  margin-bottom: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #f9fafb;
}

.thinking-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
}

.thinking-header:hover {
  background: #f0f2f5;
}

.thinking-title {
  flex: 1;
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.expand-icon {
  transition: transform 0.3s;
  color: #909399;
}

.expand-icon.expanded {
  transform: rotate(180deg);
}

.thinking-content {
  padding: 0 12px 12px;
  max-height: 300px;
  overflow-y: auto;
}

.thinking-step {
  display: flex;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px dashed #e4e7ed;
  font-size: 13px;
}

.thinking-step:last-child {
  border-bottom: none;
}

.step-agent {
  color: #409EFF;
  font-weight: 500;
  min-width: 60px;
}

.step-message {
  color: #606266;
  flex: 1;
}

/* 流式内容区域样式 */
.streaming-content {
  padding: 12px;
  background: #fff;
  border-radius: 6px;
  margin-top: 8px;
  border: 1px solid #e4e7ed;
}

.loading {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.input-area {
  padding: 24px;
  border-top: 1px solid #e4e7ed;
  background: #fff;
}

.input-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}

.right-sidebar {
  width: 300px;
  background: #fff;
  border-left: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  transition: width 0.3s;
  position: relative;
}

.right-sidebar.collapsed {
  width: 40px;
  border-left: 1px solid #e4e7ed;
  overflow: hidden;
}

.expand-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  cursor: pointer;
  color: #909399;
  font-size: 20px;
  transition: all 0.3s;
}

.expand-button:hover {
  color: #409eff;
  background: #f5f7fa;
}

.file-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.file-item {
  display: flex;
  align-items: center;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 8px;
  transition: background 0.2s;
}

.file-item:hover {
  background: #f5f7fa;
}

.file-info {
  flex: 1;
  margin-left: 12px;
}

.file-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.file-size {
  font-size: 12px;
  color: #909399;
}

/* 文件树样式 */
.file-tree-node {
  margin: 2px 0;
}

.node-content {
  display: flex;
  align-items: center;
  padding: 6px 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
  gap: 6px;
  font-size: 13px;
}

.node-content .el-icon {
  width: 16px;
  height: 16px;
  font-size: 16px;
}

.node-content .el-icon svg {
  width: 16px;
  height: 16px;
}

.node-content:hover {
  background: #f5f7fa;
}

.node-content.is-folder {
  font-weight: 500;
}

.node-content.is-folder.expanded {
  color: #409EFF;
}

.expand-arrow {
  font-size: 10px;
  color: #909399;
  transition: transform 0.2s;
}

.expand-arrow.expanded {
  transform: rotate(0deg);
}

.node-name {
  flex: 1;
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.download-icon {
  opacity: 0;
  transition: opacity 0.2s;
  cursor: pointer;
  color: #409EFF;
}

.node-content:hover .download-icon {
  opacity: 1;
}

.node-children {
  border-left: 1px solid #e4e7ed;
  margin-left: 16px;
  padding-left: 4px;
}
</style>
