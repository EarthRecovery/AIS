import request from '@/utils/request'

// 真实推演（沙盘）：每步要调多次 LLM，远超全局 10s 超时，这里单独放宽。
const STEP = { timeout: 180000 }      // 单轮 / 开场景：3 分钟
const DAY = { timeout: 900000 }       // 自动跑完一天（多幕多轮）：15 分钟

const BASE_URL = request.defaults.baseURL || ''

// 通用 SSE：POST 一个 JSON body，逐条解析 `data: {...}` 事件交给 onEvent。
async function ssePost(path, body, onEvent) {
  const token = localStorage.getItem('ais_token')
  if (!token) { window.location.href = '/login'; throw new Error('Not authenticated') }
  const resp = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify(body || {}),
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

// 流式跑一轮：逐 token 吐发言，事件 speaker/token/speaker_done/judge/done/scene/error
export function simStepStream(worldId, directive, onEvent) {
  return ssePost(`/world/${worldId}/sim/step/stream`, { directive: directive || '' }, onEvent)
}

// 流式「自动演完本场景」：事件同 step（scene/speaker/token/speaker_done/judge/done/error）
export function simRunSceneStream(worldId, directive, onEvent) {
  return ssePost(`/world/${worldId}/sim/run-scene/stream`, { directive: directive || '' }, onEvent)
}

// 流式「自动演完本章」：事件同上，可能含多个 scene
export function simRunChapterStream(worldId, directive, onEvent) {
  return ssePost(`/world/${worldId}/sim/run-chapter/stream`, { directive: directive || '' }, onEvent)
}

// 流式生成大纲：事件 token / done(含 outline) / error
export function genOutlineStream(worldId, directive, onEvent) {
  return ssePost(`/world/${worldId}/outline/generate/stream`, { directive: directive || '' }, onEvent)
}

export const simStatus = (worldId) => request.get(`/world/${worldId}/sim/status`)
export const simOpenScene = (worldId, directive) => request.post(`/world/${worldId}/sim/scene`, { directive }, STEP)
export const simStep = (worldId, directive) => request.post(`/world/${worldId}/sim/step`, { directive }, STEP)
export const simNewChapter = (worldId, directive) => request.post(`/world/${worldId}/sim/new-chapter`, { directive }, STEP)
export const simRunChapter = (worldId, directive) => request.post(`/world/${worldId}/sim/run-chapter`, { directive }, DAY)
export const simRunScene = (worldId, directive) => request.post(`/world/${worldId}/sim/run-scene`, { directive }, DAY)
export const simRollback = (worldId) => request.post(`/world/${worldId}/sim/rollback`)
export const simSceneMessages = (sceneId) => request.get(`/world/scene/${sceneId}/messages`)
export const charDetail = (worldId, charId) => request.get(`/world/${worldId}/character/${charId}/detail`)
export const genOutline = (worldId, directive) => request.post(`/world/${worldId}/outline/generate`, { directive }, { timeout: 120000 })
export const updateOutline = (worldId, outline) => request.patch(`/world/${worldId}/outline`, { outline })
export const updateCharacter = (charId, payload) => request.patch(`/world/character/${charId}`, payload)
export const upsertMental = (charId, payload) => request.put(`/world/character/${charId}/mental`, payload)

// 叙事层：让叙事/编剧 agent 为当前章生成「剧本/节奏」(script)，写入 outline 供 Keeper 执行
export const genScript = (worldId, directive) => request.post(`/world/${worldId}/script/generate`, { directive }, { timeout: 120000 })
// 写作层：章节列表 / 单章摘要 / 把一或多章写成小说散文
export const listChapters = (worldId) => request.get(`/world/${worldId}/chapters`)
export const chapterSummary = (worldId, label) => request.post(`/world/${worldId}/chapter/summary`, { label }, { timeout: 120000 })
export const writeChapters = (worldId, labels) => request.post(`/world/${worldId}/write`, { labels }, { timeout: 600000 })
export const listManuscripts = (worldId) => request.get(`/world/${worldId}/manuscripts`)
