import request from '@/utils/request'

export function getRoleList() {
  return request.get('/role/list')
}

// 新建 / 更新一个角色人格模板（后端按 name upsert）
export function setRole(payload) {
  return request.post('/role/set', payload)
}
