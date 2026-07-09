import axios from 'axios'

// 动态 API 地址：开发环境用 localhost:8000，生产环境用空（同域反向代理）
const apiBase = import.meta.env.VITE_API_BASE || ''
const apiTimeout = 15000

const api = axios.create({
  baseURL: apiBase + '/api',
  timeout: apiTimeout,
})

// 上传文件用单独的 axios 实例（上传可能耗时更长）
const uploadClient = axios.create({
  baseURL: apiBase,
  timeout: 30000,
})

// ===== API 方法 =====

export const lostItemsApi = {
  getAll: (params) => api.get('/lost-items', { params }),
  getById: (id) => api.get(`/lost-items/${id}`),
  create: (data) => api.post('/lost-items', data),
  update: (id, data) => api.put(`/lost-items/${id}`, data),
  delete: (id) => api.delete(`/lost-items/${id}`),
  search: (params) => api.get('/search', { params }),
  semanticSearch: (params) => api.get('/semantic-search', { params }),
}

export const usersApi = {
  getAll: () => api.get('/users'),
  getById: (id) => api.get(`/users/${id}`),
  create: (data) => api.post('/users', data),
}

export const statsApi = {
  get: () => api.get('/stats'),
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
