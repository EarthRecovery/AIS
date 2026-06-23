import request from '@/utils/request'

// 真实推演（沙盘）
export const simStatus = (worldId) => request.get(`/world/${worldId}/sim/status`)
export const simOpenScene = (worldId, directive) => request.post(`/world/${worldId}/sim/scene`, { directive })
export const simStep = (worldId, directive) => request.post(`/world/${worldId}/sim/step`, { directive })
export const simRunDay = (worldId, directive) => request.post(`/world/${worldId}/sim/run-day`, { directive })
export const simRollbackDay = (worldId) => request.post(`/world/${worldId}/sim/rollback-day`)
