import request from './request'

// 反诈问答
export function getChatSessions() {
  return request.get('/api/v1/af/chat/sessions')
}

export function createChatSession(title = '反诈咨询') {
  return request.post('/api/v1/af/chat/sessions', { title })
}

export function getChatMessages(sessionId) {
  return request.get(`/api/v1/af/chat/sessions/${sessionId}/messages`)
}

export function sendChatMessage(sessionId, content) {
  return request.post('/api/v1/af/chat/chat', { session_id: sessionId, content })
}

// 诈骗检测
export function detectText(content) {
  return request.post('/api/v1/af/detect/text', { content })
}

export function detectImage(file, description) {
  const formData = new FormData()
  formData.append('file', file)
  if (description) formData.append('description', description)
  return request.post('/api/v1/af/detect/image', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function getDetectionHistory(page = 1, pageSize = 20) {
  return request.get('/api/v1/af/detect/history', { params: { page, page_size: pageSize } })
}

// 反诈案例
export function getCaseList(params = {}) {
  return request.get('/api/v1/af/case/list', { params })
}

export function getCaseDetail(id) {
  return request.get(`/api/v1/af/case/detail/${id}`)
}

export function getCaseTypes() {
  return request.get('/api/v1/af/case/types')
}

export function syncCasesFromKnowledge() {
  return request.post('/api/v1/af/case/sync-from-knowledge')
}
