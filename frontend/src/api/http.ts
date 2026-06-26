import axios from 'axios'

const TOKEN_KEY = 'sitp_access_token'

const http = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

// Request interceptor: inject JWT token
http.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// Response interceptor: retry on network error, handle 401
http.interceptors.response.use(
  (res) => res,
  async (error) => {
    // Handle 401 Unauthorized - redirect to login
    if (error.response?.status === 401) {
      localStorage.removeItem(TOKEN_KEY)
      // Only redirect if not already on login/register page
      const path = window.location.pathname
      if (path !== '/login' && path !== '/register') {
        window.location.href = '/login'
      }
      return Promise.reject(error)
    }

    // Retry on network errors (up to 2 retries)
    const config = error.config
    if (!config || error.response || config.__retryCount >= 2) {
      return Promise.reject(error)
    }
    config.__retryCount = (config.__retryCount || 0) + 1
    await new Promise((r) => setTimeout(r, 1000 * config.__retryCount))
    return http(config)
  },
)

export default http
