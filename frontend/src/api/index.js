import axios from 'axios'
import { ElMessage } from 'element-plus'

// 动态 API 地址：开发环境用 localhost:8000，生产环境用空（同域反向代理）
const apiBase = import.meta.env.VITE_API_BASE || ''
const apiTimeout = 60000

const api = axios.create({
  baseURL: apiBase + '/api',
  timeout: apiTimeout,
  withCredentials: true,
})

// 上传文件用单独的 axios 实例（上传可能耗时更长）
const uploadClient = axios.create({
  baseURL: apiBase,
  timeout: 30000,
  withCredentials: true,
})

// 请求拦截器
api.interceptors.request.use(config => config, error => Promise.reject(error))

// 响应拦截器
api.interceptors.response.use(
  response => response,
  error => {
    if (error.config?.silent) {
      return Promise.reject(error)
    }

    const status = error.response ? error.response.status : null
    if (status === 401) {
      // 401交由路由守卫处理，不全局报错以防止 /auth/me 首次加载出错
    } else if (status === 403) {
      ElMessage.error('您没有权限执行此操作')
    } else if (status >= 500) {
      ElMessage.error('服务器内部错误，请稍后再试')
    } else if (status === 400 || status === 422) {
      const msg = error.response.data?.detail || '请求参数错误'
      if (typeof msg === 'string') {
        ElMessage.warning(msg)
      } else {
        ElMessage.warning('请求参数错误')
      }
    } else if (error.code !== 'ERR_CANCELED') {
      ElMessage.error('网络请求失败，请检查网络连接')
    }
    return Promise.reject(error)
  }
)

// ===== API 方法 =====

export const lostItemsApi = {
  getAll: (params, config = {}) => api.get('/lost-items', { params, ...config }),
  getById: (id) => api.get(`/lost-items/${id}`),
  create: (data) => api.post('/lost-items', data),
  matchCheck: (data) => api.post('/match-check', data),
  update: (id, data) => api.put(`/lost-items/${id}`, data),
  delete: (id) => api.delete(`/lost-items/${id}`),
  search: (params) => api.get('/search', { params }),
  semanticSearch: (params) => api.get('/semantic-search', { params }),
}

export const usersApi = {
  getAll: () => api.get('/users'),
  getById: (id) => api.get(`/users/${id}`),
  create: (data) => api.post('/users', data),
  update: (id, data) => api.put(`/users/${id}`, data),
}

export const statsApi = {
  get: () => api.get('/stats'),
}

export const authApi = {
  loginUrl: (next = '/') => `${apiBase}/api/auth/login?next=${encodeURIComponent(next)}`,
  me: (config = {}) => api.get('/auth/me', config),
  logout: () => api.post('/auth/logout'),
  updateProfile: (data) => api.put('/auth/profile', data),
}

export const meApi = {
  get: () => api.get('/me'),
  update: (data) => api.put('/me', data),
  items: (params) => api.get('/me/items', { params }),
}

export const uploadApi = {
  uploadImage: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return uploadClient.post('/api/upload', formData)
  },
}

/**
 * 将后端返回的相对路径或 localhost URL 转为可访问的完整 URL
 * 开发环境：http://localhost:8000/uploads/xxx.png → 保持
 * 生产环境：/uploads/xxx.png → 同域，保持不变
 */
export function resolveImageUrl(url) {
  if (!url) return ''
  // 已经是绝对 URL（含协议）→ 直接返回
  if (url.startsWith('http://') || url.startsWith('https://')) {
    // 开发环境下 localhost URL 保持不变；生产环境下不应出现 localhost
    return url
  }
  // 相对路径 → 拼接 API base
  if (url.startsWith('/')) {
    return apiBase + url
  }
  return url
}

export { apiBase }
export default api
