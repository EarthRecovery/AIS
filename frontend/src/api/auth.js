import request from '@/utils/request'

export function login(payload) {
  return request.post('/auth/login', payload)
}

export function register(payload) {
  return request.post('/auth/register', payload)
}

export const me = () => request.get('/auth/me')

// 管理员：LLM 调用日志
export const listLlmLogs = (params) => request.get('/auth/llm-logs', { params })
export const getLlmLog = (id) => request.get(`/auth/llm-logs/${id}`)
export const clearLlmLogs = () => request.delete('/auth/llm-logs')
