import request from '@/utils/request'

// 真实推演（沙盘）：每步要调多次 LLM，远超全局 10s 超时，这里单独放宽。
const STEP = { timeout: 180000 }      // 单轮 / 开场景：3 分钟
const DAY = { timeout: 900000 }       // 自动跑完一天（多幕多轮）：15 分钟

const BASE_URL = request.defaults.baseURL || ''

// 流式跑一轮：逐 token 吐发言，事件 speaker/token/speaker_done/judge/done/scene/error
export async function simStepStream(worldId, directive, onEvent) {
  const token = localStorage.getItem('ais_token')
  if (!token) { window.location.href = '/login'; throw new Error('Not authenticated') }
  const resp = await fetch(`${BASE_URL}/world/${worldId}/sim/step/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({ directive: directive || '' }),
  })
  if (!resp.ok || !resp.body) throw new Error(`stream failed: ${resp.status}`)
  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  const handle = (raw) => {
    if (!raw.startsWith('data:')) return
    const payload = raw.slice(5).trim()
    if (!payload) return
    try { onEvent(JSON.parse(payload)) } catch (e) { /* ignore */ }
  }
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    let b
    while ((b = buffer.search(/\r\n\r\n/)) !== -1) {
      handle(buffer.slice(0, b))
      buffer = buffer.slice(b + 4)
    }
  }
  if (buffer.trim()) handle(buffer.trim())
}

export const simStatus = (worldId) => request.get(`/world/${worldId}/sim/status`)
export const simOpenScene = (worldId, directive) => request.post(`/world/${worldId}/sim/scene`, { directive }, STEP)
export const simStep = (worldId, directive) => request.post(`/world/${worldId}/sim/step`, { directive }, STEP)
export const simRunDay = (worldId, directive) => request.post(`/world/${worldId}/sim/run-day`, { directive }, DAY)
export const simRollbackDay = (worldId) => request.post(`/world/${worldId}/sim/rollback-day`)
export const simSceneMessages = (sceneId) => request.get(`/world/scene/${sceneId}/messages`)
export const genOutline = (worldId, directive) => request.post(`/world/${worldId}/outline/generate`, { directive }, { timeout: 120000 })
