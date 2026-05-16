import request from './request'

// 获取所有设置
export function getSettings() {
  return request.get('/api/v1/settings/list')
}

// 获取单个设置
export function getSetting(key) {
  return request.get(`/api/v1/settings/${key}`)
}

// 更新单个设置
export function updateSetting(key, value) {
  return request.put(`/api/v1/settings/${key}`, null, { params: { value } })
}

// 批量更新设置
export function batchUpdateSettings(settings) {
  return request.post('/api/v1/settings/batch', settings)
}

// 初始化默认设置
export function initSettings() {
  return request.post('/api/v1/settings/init')
}

// 测试LLM连接
export function testLLMConnection(config) {
  return request.post('/api/v1/settings/test-llm', config)
}
