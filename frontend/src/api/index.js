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

export const notificationsApi = {
  list: (params) => api.get('/notifications', { params, silent: true }),
  unreadCount: () => api.get('/notifications/unread-count', { silent: true }),
  markRead: (id) => api.put(`/notifications/${id}/read`, null, { silent: true }),
}

export const claimsApi = {
  create: (itemId, data) => api.post(`/lost-items/${itemId}/claim`, data),
  mine: () => api.get('/me/claims'),
  adminList: (params) => api.get('/claim-requests', { params }),
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
  analyzeImages: (imageUrls, config = {}) => api.post('/image-analysis', { image_urls: imageUrls }, config),
}

function sameOriginUploadUrl(url) {
  try {
    const parsed = new URL(url, window.location.origin)
    const apiOrigin = apiBase ? new URL(apiBase, window.location.origin).origin : window.location.origin
    if (parsed.origin !== apiOrigin || !parsed.pathname.startsWith('/uploads/')) return ''
    return apiBase && parsed.origin === window.location.origin ? apiBase + parsed.pathname : parsed.href
  } catch {
    return ''
  }
}

/**
 * 只渲染本站上传目录下的图片，避免第三方图片 URL 造成访问信息泄露。
 */
export function resolveImageUrl(url) {
  const value = String(url || '').trim()
  if (!value) return ''
  if (value.startsWith('/uploads/')) return apiBase + value
  if (value.startsWith('uploads/')) return apiBase + `/${value}`
  return sameOriginUploadUrl(value)
}

export function firstSafeImageUrl(urls) {
  if (!urls) return ''
  for (const rawUrl of String(urls).split(',')) {
    const resolved = resolveImageUrl(rawUrl)
    if (resolved) return resolved
  }
  return ''
}

export { apiBase }
export default api
