import request from '@/utils/request'
const BASE_URL = request.defaults.baseURL || ''

export function sendChatMessage(message) {
  return request.post('/chat', {
    message
  })
}

export async function streamChatMessage(message, onChunk) {
  const resp = await fetch(`${BASE_URL}/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ message })
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

export function getCurrentTurnId() {
  return request.get('/chat/turnid')
}

export function getHistoryByTurnId(turn_id) {
  return request.get(`/chat/history/${turn_id}`)
}

export function startNewChat() {
  return request.get('/chat/new')
}
