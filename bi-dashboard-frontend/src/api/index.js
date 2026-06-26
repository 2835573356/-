import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' }
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  response => {
    const body = response.data
    // Backend returns { code, data, message }
    if (body && body.code !== undefined) {
      if (body.code === 0) {
        return body.data
      }
      // Auth error — redirect to login
      if (body.code === 40100) {
        localStorage.removeItem('token')
        window.location.href = '/login'
      }
      return Promise.reject(new Error(body.message || '请求失败'))
    }
    return body
  },
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    // FastAPI returns { detail: "..." }, our backend returns { message: "..." }
    const msg = error.response?.data?.detail
      || error.response?.data?.message
      || error.message
      || '网络错误'
    const err = new Error(msg)
    err.status = error.response?.status
    return Promise.reject(err)
  }
)

export default api

/** Map English sentiment values from DB to Chinese display */
export function sentimentToChinese(val) {
  const map = { negative: '消极', neutral: '中性', positive: '积极' }
  return map[val] || val || '未知'
}

/** Map Chinese sentiment to English for API filters */
export function sentimentToEnglish(val) {
  const map = { '消极': 'negative', '中性': 'neutral', '积极': 'positive' }
  return map[val] || val
}
