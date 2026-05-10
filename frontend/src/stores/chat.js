import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useChatStore = defineStore('chat', () => {
  const sessions = ref([])
  const currentSessionId = ref(null)
  const messages = ref([])
  const files = ref([])
  const fileTree = ref([])

  function setSessions(sessionList) {
    sessions.value = sessionList
  }

  function addSession(session) {
    sessions.value.push(session)
  }

  function setCurrentSession(sessionId) {
    currentSessionId.value = sessionId
  }

  function setMessages(msgList) {
    messages.value = msgList
  }

  function addMessage(message) {
    messages.value.push(message)
  }

  function setFiles(fileList) {
    files.value = fileList
  }

  function addFile(file) {
    files.value.push(file)
  }

  function setFileTree(tree) {
    fileTree.value = tree
  }

  function clearCurrentChat() {
    currentSessionId.value = null
    messages.value = []
    files.value = []
    fileTree.value = []
  }

  return {
    sessions,
    currentSessionId,
    messages,
    files,
    fileTree,
    setSessions,
    addSession,
    setCurrentSession,
    setMessages,
    addMessage,
    setFiles,
    addFile,
    setFileTree,
    clearCurrentChat
  }
})
