import axios from 'axios'

const http = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

http.interceptors.response.use(
  (res) => res,
  async (error) => {
    const config = error.config
    if (!config || config.__retryCount >= 2) {
      return Promise.reject(error)
    }
    config.__retryCount = (config.__retryCount || 0) + 1
    await new Promise((r) => setTimeout(r, 1000 * config.__retryCount))
    return http(config)
  },
)

export default http
