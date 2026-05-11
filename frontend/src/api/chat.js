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

// 发送消息（SSE 流式）- 返回原始 Response 对象用于流式读取
export function sendMessageStream(sessionId, content) {
  return request({
    url: '/chat/send',
    method: 'post',
    data: {
      session_id: sessionId,
      content
    },
    responseType: 'stream' // 关键：设置为 stream 以获取原始响应流
  })
}

// 发送消息（兼容旧接口）
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
