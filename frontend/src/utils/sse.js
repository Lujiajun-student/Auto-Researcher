/**
 * SSE (Server-Sent Events) 解析工具类
 * 用于处理流式服务器发送事件
 */

/**
 * SSE 事件解析器类
 */
export class SSEParser {
  constructor(options = {}) {
    this.buffer = ''
    this.decoder = new TextDecoder('utf-8')
    this.onEvent = options.onEvent || (() => {})
    this.onError = options.onError || (() => {})
    this.onComplete = options.onComplete || (() => {})
    this.debug = options.debug || false
  }

  /**
   * 解析 SSE 数据块
   * @param {Uint8Array} chunk - 二进制数据块
   */
  parseChunk(chunk) {
    try {
      const text = this.decoder.decode(chunk, { stream: true })
      this.buffer += text

      // 按行分割
      const lines = this.buffer.split('\n')
      // 保留最后一个可能不完整的行
      this.buffer = lines.pop() || ''

      // 处理每一行
      for (const line of lines) {
        this.parseLine(line)
      }
    } catch (error) {
      this.logError('解析数据块失败', error)
    }
  }

  /**
   * 解析单行 SSE 数据
   * @param {string} line - SSE 数据行
   */
  parseLine(line) {
    const trimmedLine = line.trim()

    // 跳过空行和注释
    if (!trimmedLine || trimmedLine.startsWith(':')) {
      return
    }

    // 解析 SSE 数据行
    if (trimmedLine.startsWith('data: ')) {
      const dataStr = trimmedLine.slice(6).trim()

      // 跳过空数据
      if (!dataStr) {
        return
      }

      try {
        const event = JSON.parse(dataStr)
        this.log('解析事件:', event)
        this.onEvent(event)
      } catch (error) {
        this.logError('解析 JSON 失败', error, dataStr)
      }
    }
  }

  /**
   * 完成解析，清空缓冲区
   */
  complete() {
    this.log('解析完成')
    this.buffer = ''
    this.onComplete()
  }

  /**
   * 重置解析器状态
   */
  reset() {
    this.buffer = ''
    this.log('解析器已重置')
  }

  /**
   * 日志输出
   */
  log(...args) {
    if (this.debug) {
      console.log('[SSE]', ...args)
    }
  }

  /**
   * 错误日志
   */
  logError(message, error, ...data) {
    console.error('[SSE]', message, error, data)
    this.onError({ message, error, data })
  }
}

/**
 * 从 Response 对象读取 SSE 流
 * @param {Response} response - Fetch API 返回的 Response 对象
 * @param {Object} callbacks - 回调函数集合
 * @param {Function} callbacks.onEvent - 事件回调
 * @param {Function} callbacks.onError - 错误回调
 * @param {Function} callbacks.onComplete - 完成回调
 * @param {boolean} callbacks.debug - 是否开启调试模式
 */
export async function readSSEStream(response, callbacks) {
  // 检查响应状态
  if (!response.ok) {
    const errorText = await response.text().catch(() => '未知错误')
    throw new Error(`HTTP ${response.status}: ${errorText}`)
  }

  // 检查是否有响应体
  if (!response.body) {
    throw new Error('响应体为空')
  }

  // 创建解析器
  const parser = new SSEParser({
    onEvent: callbacks.onEvent,
    onError: callbacks.onError,
    onComplete: callbacks.onComplete,
    debug: callbacks.debug
  })

  // 读取流
  const reader = response.body.getReader()

  try {
    while (true) {
      const { done, value } = await reader.read()

      if (done) {
        parser.complete()
        break
      }

      parser.parseChunk(value)
    }
  } catch (error) {
    parser.logError('读取流失败', error)
    callbacks.onError?.(error)
    throw error
  } finally {
    reader.releaseLock()
  }
}

/**
 * 创建 SSE 连接并读取流
 * @param {string} url - SSE 端点 URL
 * @param {Object} options - 请求选项
 * @param {Object} callbacks - 回调函数集合
 */
export async function createSSEConnection(url, options = {}, callbacks = {}) {
  const {
    method = 'POST',
    headers = {},
    body = null
  } = options

  const defaultHeaders = {
    'Content-Type': 'application/json',
    ...headers
  }

  const response = await fetch(url, {
    method,
    headers: defaultHeaders,
    body: body ? JSON.stringify(body) : null
  })

  await readSSEStream(response, callbacks)
}

export default {
  SSEParser,
  readSSEStream,
  createSSEConnection
}
