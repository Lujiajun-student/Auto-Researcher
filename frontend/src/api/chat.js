import request from '@/utils/request'

// 获取会话列表
export function getSessions() {
  return request({
    url: '/chat/sessions',
    method: 'get'
  })
}

// 创建新会话
export function createSession(title) {
  return request({
    url: '/chat/sessions',
    method: 'post',
    data: { title }
  })
}

// 删除会话
export function deleteSession(sessionId) {
  return request({
    url: `/chat/sessions/${sessionId}`,
    method: 'delete'
  })
}

// 获取会话消息
export function getMessages(sessionId) {
  return request({
    url: `/chat/sessions/${sessionId}/messages`,
    method: 'get'
  })
}

// 发送消息（SSE 流式）
export function sendMessage(sessionId, content) {
  return request({
    url: '/chat/send',
    method: 'post',
    data: {
      session_id: sessionId,
      content
    }
  })
}

// 获取文件列表
export function getFiles(sessionId) {
  return request({
    url: `/chat/sessions/${sessionId}/files`,
    method: 'get'
  })
}

// 下载文件
export function downloadFile(fileId) {
  return request({
    url: `/chat/files/${fileId}`,
    method: 'get',
    responseType: 'blob'
  })
}
