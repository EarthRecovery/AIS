import request from '@/utils/request'

// ---- World ----
export const listWorlds = () => request.get('/world/list')
export const createWorld = (payload) => request.post('/world/new', payload)
export const getWorld = (id) => request.get(`/world/${id}`)
export const updateWorld = (id, payload) => request.patch(`/world/${id}`, payload)
export const deleteWorld = (id) => request.delete(`/world/${id}`)
export const getWorldEvents = (id) => request.get(`/world/${id}/events`)

// ---- Worldview ----
export const listWorldviews = () => request.get('/world/worldview/list')
export const updateWorldview = (id, payload) => request.patch(`/world/worldview/${id}`, payload)
// 世界观按用户共享，复用 communication 的创建接口
export const createWorldview = (payload) => request.post('/communication/worldview', payload)

// ---- Character ----
export const createCharacter = (worldId, payload) => request.post(`/world/${worldId}/character`, payload)
export const updateCharacter = (id, payload) => request.patch(`/world/character/${id}`, payload)
export const deleteCharacter = (id) => request.delete(`/world/character/${id}`)
export const upsertMental = (charId, payload) => request.put(`/world/character/${charId}/mental`, payload)

// ---- Ability ----
export const createAbility = (charId, payload) => request.post(`/world/character/${charId}/ability`, payload)
export const updateAbility = (id, payload) => request.patch(`/world/ability/${id}`, payload)
export const deleteAbility = (id) => request.delete(`/world/ability/${id}`)

// ---- Belief ----
export const createBelief = (worldId, payload) => request.post(`/world/${worldId}/belief`, payload)
export const updateBelief = (id, payload) => request.patch(`/world/belief/${id}`, payload)
export const deleteBelief = (id) => request.delete(`/world/belief/${id}`)

// ---- Location ----
export const createLocation = (worldId, payload) => request.post(`/world/${worldId}/location`, payload)
export const updateLocation = (id, payload) => request.patch(`/world/location/${id}`, payload)
export const deleteLocation = (id) => request.delete(`/world/location/${id}`)

// ---- Item ----
export const createItem = (worldId, payload) => request.post(`/world/${worldId}/item`, payload)
export const updateItem = (id, payload) => request.patch(`/world/item/${id}`, payload)
export const deleteItem = (id) => request.delete(`/world/item/${id}`)

// ---- Relationship ----
export const createRelationship = (worldId, payload) => request.post(`/world/${worldId}/relationship`, payload)
export const updateRelationship = (id, payload) => request.patch(`/world/relationship/${id}`, payload)
export const deleteRelationship = (id) => request.delete(`/world/relationship/${id}`)
