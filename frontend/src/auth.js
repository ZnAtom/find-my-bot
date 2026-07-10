import { reactive } from 'vue'
import { authApi } from './api'

const VIEW_KEY = 'foundit_view_mode'

const state = reactive({
  user: null,
  loaded: false,
  loading: false,
  viewMode: localStorage.getItem(VIEW_KEY) || 'user',
})

let restorePromise = null

async function restoreSession() {
  if (!restorePromise) {
    restorePromise = (async () => {
      state.loading = true
      try {
        const res = await authApi.me()
        state.user = res.data.user
        // 非管理员强制 user 视角
        if (state.user?.role !== 'admin') {
          state.viewMode = 'user'
          localStorage.removeItem(VIEW_KEY)
        }
      } catch {
        state.user = null
      } finally {
        state.loaded = true
        state.loading = false
        restorePromise = null
      }
    })()
  }
  return restorePromise
}

function loginWithCasdoor(next = window.location.pathname + window.location.search + window.location.hash) {
  window.location.href = authApi.loginUrl(next || '/')
}

async function logout() {
  try {
    await authApi.logout()
  } finally {
    state.user = null
    state.viewMode = 'user'
    localStorage.removeItem(VIEW_KEY)
  }
}

function toggleView() {
  if (state.user?.role !== 'admin') return
  state.viewMode = state.viewMode === 'admin' ? 'user' : 'admin'
  localStorage.setItem(VIEW_KEY, state.viewMode)
}

async function updateProfile(data) {
  const res = await authApi.updateProfile(data)
  state.user = res.data
  return res.data
}

export const auth = {
  state,
  restoreSession,
  loginWithCasdoor,
  logout,
  toggleView,
  updateProfile,
  get user() {
    return state.user
  },
  get isLoggedIn() {
    return Boolean(state.user)
  },
  // 后端真实角色
  get isAdmin() {
    return state.user?.role === 'admin'
  },
  // 当前生效的角色（受视角切换影响）
  get effectiveRole() {
    if (state.user?.role !== 'admin') return state.user?.role || 'user'
    return state.viewMode
  },
  get isAdminView() {
    return state.user?.role === 'admin' && state.viewMode === 'admin'
  },
  get viewLabel() {
    if (state.user?.role !== 'admin') return '普通用户'
    return state.viewMode === 'admin' ? '管理员视角' : '普通用户预览'
  },
}

export default auth
