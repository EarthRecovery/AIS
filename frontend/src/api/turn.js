import request from '@/utils/request'

export function getTurnHistory() {
  return request({
    url: '/turns/history',
    method: 'get'
  })
}

export function agentChangeToTurn(turn_id) {
    return request.post(`/turns/change/${turn_id}`)
}
