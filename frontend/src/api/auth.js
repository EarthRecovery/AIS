import request from '@/utils/request'

export function login(payload) {
  return request.post('/auth/login', payload)
}

export function register(payload) {
  return request.post('/auth/register', payload)
}
