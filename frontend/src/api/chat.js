import request from '@/utils/request'
const BASE_URL = request.defaults.baseURL || ''

export function sendChatMessage(message, history_id) {
  return request.post('/chat', {
    message,
    history_id,
  })
}

function decodeStreamPayload(payload) {
  let chunk
  try {
    chunk = JSON.parse(payload)
  } catch (e) {
    chunk = payload
  }
  if (typeof chunk !== 'string') {
    chunk = chunk != null ? String(chunk) : ''
  }
  // strip accidental wrapping quotes like "\"你好\""
  if (chunk.startsWith('"') && chunk.endsWith('"')) {
    chunk = chunk.slice(1, -1)
  }
  // normalize escaped newlines/tabs that may leak through double-encoded payloads
  // handle double-escaped first, then single-escaped
  chunk = chunk.replace(/\\\\n/g, '\n').replace(/\\\\t/g, '\t')
  chunk = chunk.replace(/\\n/g, '\n').replace(/\\t/g, '\t')
  // sometimes model may emit literal "/n"
  chunk = chunk.replace(/\/n/g, '\n')
  return chunk
}

function trimSpacesOnly(str) {
  // remove leading/trailing spaces and tabs but preserve newlines
  return str.replace(/^[ \t]+|[ \t]+$/g, '')
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

    // 支持 \r\n\r\n 边界
    let boundary
    while ((boundary = buffer.search(/\r\n\r\n/)) !== -1) {
      console.log(
        'buffer:',
        buffer
          .replace(/\r/g, '\\r')
          .replace(/\n/g, '\\n')
      )

      const raw = buffer.slice(0, boundary)
      console.log(
        'raw:',
        raw
          .replace(/\r/g, '\\r')
          .replace(/\n/g, '\\n')
      )
      
      buffer = buffer.slice(boundary + 4) // skip the boundary
      if(!raw.startsWith('data:')) {
        // Not a data line; skip
        continue
      }
      let payload = raw.slice(5)
      const chunk = trimSpacesOnly(decodeStreamPayload(payload))
      fullText += chunk
      if (onChunk) onChunk(chunk)
    }
    
  }

  // Flush any remaining buffered content
  const tail = buffer
  if (tail.startsWith('data:')) {
    let payload = tail.slice(5)
    if (payload.startsWith(' ')) payload = payload.slice(1)
    const chunk = trimSpacesOnly(decodeStreamPayload(payload))
    fullText += chunk
    if (onChunk) onChunk(chunk)
  }

  console.log('Full streamed text:', fullText)

  return fullText
}

export function getHistoryByHistoryId(history_id) {
  return request.get(`/chat/history/${history_id}`)
}

export function startNewChat(roleId) {
  const selected = roleId || 1
  return request.get(`/chat/new/${selected}`)
}
