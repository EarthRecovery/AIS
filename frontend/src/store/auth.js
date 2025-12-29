import { defineStore } from 'pinia'
import { login as loginApi, register as registerApi } from '@/api/auth'

const TOKEN_KEY = 'ais_token'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem(TOKEN_KEY) || '',
    user: null,
  }),
  actions: {
    setToken(token) {
      this.token = token || ''
      if (token) {
        localStorage.setItem(TOKEN_KEY, token)
      } else {
        localStorage.removeItem(TOKEN_KEY)
      }
    },
    loadFromStorage() {
      this.token = localStorage.getItem(TOKEN_KEY) || ''
    },
    logout() {
      this.setToken('')
      this.user = null
    },
    async login(payload) {
      const resp = await loginApi({
        email: payload.email?.trim() || undefined,
        phone_number: payload.phone_number?.trim() || undefined,
        password: payload.password,
      })
      const data = resp?.data || {}
      // 优先读取响应头里的 Authorization: Bearer xxx
      const headerToken = resp?.headers?.authorization || resp?.headers?.Authorization || resp?.headers?.token
      const tokenFromHeader = headerToken ? headerToken.replace(/Bearer\s+/i, '') : ''
      const token = tokenFromHeader || data?.token || data?.access_token || data?.jwt

      if (!token) {
        throw new Error('登录成功但未返回 token')
      }
      this.setToken(token)
      this.user = data
      return data
    },
    async register(payload) {
      const { data } = await registerApi({
        name: payload.name,
        email: payload.email?.trim() || undefined,
        phone_number: payload.phone_number?.trim() || undefined,
        password: payload.password,
      })
      return data
    },
  },
})
