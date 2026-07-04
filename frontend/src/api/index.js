import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 10000
})

export const lostItemsApi = {
  getAll: (params) => api.get('/lost-items', { params }),
  getById: (id) => api.get(`/lost-items/${id}`),
  create: (data) => api.post('/lost-items', data),
  update: (id, data) => api.put(`/lost-items/${id}`, data),
  delete: (id) => api.delete(`/lost-items/${id}`),
  search: (params) => api.get('/search', { params }),
  semanticSearch: (params) => api.get('/semantic-search', { params })
}

export const usersApi = {
  getAll: () => api.get('/users'),
  getById: (id) => api.get(`/users/${id}`),
  create: (data) => api.post('/users', data)
}

export const statsApi = {
  get: () => api.get('/stats')
}

export default api