import request from '@/utils/request'

const BASE_URL = request.defaults.baseURL || ''

// ---------------- 世界观 ----------------
export function listWorldviews() {
  return request.get('/communication/worldview/list')
}

export function createWorldview(payload) {
  return request.post('/communication/worldview', payload)
}

// ---------------- 房间 ----------------
export function listRooms() {
  return request.get('/communication/room/list')
}

export function createRoom(payload) {
  return request.post('/communication/room/new', payload)
}

export function getRoomDetail(roomId) {
  return request.get(`/communication/room/${roomId}`)
}

export function deleteRoom(roomId) {
  return request.delete(`/communication/room/${roomId}`)
}

// ---------------- SSE：发言 / 推进 ----------------
// 后端每个事件是一行 `data: {json}\r\n\r\n`，事件类型：speaker / token / done / error
async function streamEvents(path, body, onEvent) {
  const token = localStorage.getItem('ais_token')
  if (!token) {
    window.location.href = '/login'
    throw new Error('Not authenticated')
  }
  const resp = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body || {}),
  })
  if (!resp.ok || !resp.body) {
    throw new Error(`Stream request failed: ${resp.status}`)
  }

  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  const handleRaw = (raw) => {
    if (!raw.startsWith('data:')) return
    const payload = raw.slice(5).trim()
    if (!payload) return
    try {
      onEvent(JSON.parse(payload))
    } catch (e) {
      console.warn('bad SSE payload', payload)
    }
  }

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    let boundary
    while ((boundary = buffer.search(/\r\n\r\n/)) !== -1) {
      const raw = buffer.slice(0, boundary)
      buffer = buffer.slice(boundary + 4)
      handleRaw(raw)
    }
  }
  if (buffer.trim()) handleRaw(buffer.trim())
}

export function streamSay(roomId, content, targetRoleId, onEvent) {
  return streamEvents(
    `/communication/room/${roomId}/say/stream`,
    { content, target_role_id: targetRoleId || null },
    onEvent
  )
}

export function streamAdvance(roomId, targetRoleId, onEvent) {
  return streamEvents(
    `/communication/room/${roomId}/advance/stream`,
    { target_role_id: targetRoleId || null },
    onEvent
  )
}
