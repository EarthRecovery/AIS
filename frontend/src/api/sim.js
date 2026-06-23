import request from '@/utils/request'

// 真实推演（沙盘）：每步要调多次 LLM，远超全局 10s 超时，这里单独放宽。
const STEP = { timeout: 180000 }      // 单轮 / 开场景：3 分钟
const DAY = { timeout: 900000 }       // 自动跑完一天（多幕多轮）：15 分钟

export const simStatus = (worldId) => request.get(`/world/${worldId}/sim/status`)
export const simOpenScene = (worldId, directive) => request.post(`/world/${worldId}/sim/scene`, { directive }, STEP)
export const simStep = (worldId, directive) => request.post(`/world/${worldId}/sim/step`, { directive }, STEP)
export const simRunDay = (worldId, directive) => request.post(`/world/${worldId}/sim/run-day`, { directive }, DAY)
export const simRollbackDay = (worldId) => request.post(`/world/${worldId}/sim/rollback-day`)
