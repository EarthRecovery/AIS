import axios from 'axios'

const request = axios.create({
  // baseURL: 'http://18.170.57.90:8000', 
  baseURL: 'http://localhost:2222',
  timeout: 10000
})

request.interceptors.request.use((config) => {
  const TOKEN_KEY = 'ais_token'
  const token = localStorage.getItem(TOKEN_KEY)
  const isAuthPath = (config.url || '').startsWith('/auth')
  if (!token && !isAuthPath) {
    window.location.href = '/login'
    return Promise.reject(new Error('Not authenticated'))
  }
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

request.interceptors.response.use(
  (resp) => resp,
  (error) => {
    if (error?.response?.status === 401) {
      localStorage.removeItem('ais_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default request
