import request from '@/utils/request'
const BASE_URL = request.defaults.baseURL || ''

export function sendChatMessage(message, history_id) {
  return request.post('/chat', {
    message,
    history_id,
  })
}

export async function streamChatMessage(message, history_id, onChunk) {
  const token = localStorage.getItem('ais_token')
  if (!token) {
    window.location.href = '/login'
    throw new Error('Not authenticated')
  }
  if (!message || !`${message}`.trim()) {
    throw new Error('message is required')
  }
  const resp = await fetch(`${BASE_URL}/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    // backend ChatRequest expects { message, history_id }
    body: JSON.stringify({ message, history_id }),
  })

  if (!resp.ok || !resp.body) {
    throw new Error(`Stream request failed: ${resp.status}`)
  }

  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let fullText = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    let boundary
    while ((boundary = buffer.indexOf('\n\n')) !== -1) {
      const raw = buffer.slice(0, boundary).trim()
      buffer = buffer.slice(boundary + 2)
      if (!raw.startsWith('data:')) continue
      const chunk = raw.slice(5).trim()
      if (!chunk) continue
      fullText += chunk
      if (onChunk) onChunk(chunk)
    }
  }

  // Flush any remaining buffered content
  const tail = buffer.trim()
  if (tail.startsWith('data:')) {
    const chunk = tail.slice(5).trim()
    fullText += chunk
    if (onChunk) onChunk(chunk)
  }

  return fullText
}

export function getHistoryByHistoryId(history_id) {
  return request.get(`/chat/history/${history_id}`)
}

export function startNewChat(roleId) {
  const selected = roleId || 1
  return request.get(`/chat/new/${selected}`)
}
