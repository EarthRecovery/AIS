import request from '@/utils/request'

export function sendChatMessage(message) {
  return request.post('/chat', {
    message
  })
}

export function getCurrentTurnId() {
  return request.get('/chat/turnid')
}

export function getHistoryByTurnId(turn_id) {
  return request.get(`/chat/history/${turn_id}`)
}

export function startNewChat() {
  return request.get('/chat/new')
}
