import request from '@/utils/request'

export function getRoleList() {
  return request.get('/role/list')
}

// 新建 / 更新一个角色人格模板（后端按 name upsert）
export function setRole(payload) {
  return request.post('/role/set', payload)
}

// 给角色添加知识库：后端分段索引并把该角色 rag_name 指向对应 collection
export function addRoleKnowledge(roleId, text) {
  return request.post(`/role/${roleId}/knowledge`, { text })
}
