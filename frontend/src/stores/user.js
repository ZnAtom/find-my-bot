import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '../api'
import { ElMessage } from 'element-plus'

const VIEW_KEY = 'foundit_view_mode'

export const useUserStore = defineStore('user', () => {
  const user = ref(null)
  const isInitialized = ref(false)
  const isLoading = ref(false)
  const viewMode = ref(localStorage.getItem(VIEW_KEY) || 'user')

  const isAuthenticated = computed(() => Boolean(user.value))
  const isAdmin = computed(() => user.value?.role === 'admin')
  
  // 当前生效的角色（受视角切换影响）
  const effectiveRole = computed(() => {
    if (user.value?.role !== 'admin') return user.value?.role || 'user'
    return viewMode.value
  })

  const isAdminView = computed(() => user.value?.role === 'admin' && viewMode.value === 'admin')

  const fetchUser = async () => {
    if (isLoading.value) return
    isLoading.value = true
    try {
      const res = await authApi.me()
      user.value = res.data.user
      if (user.value?.role !== 'admin') {
        viewMode.value = 'user'
        localStorage.removeItem(VIEW_KEY)
      }
    } catch (err) {
      user.value = null
    } finally {
      isInitialized.value = true
      isLoading.value = false
    }
  }

  const logout = async () => {
    try {
      await authApi.logout()
    } finally {
      user.value = null
      viewMode.value = 'user'
      localStorage.removeItem(VIEW_KEY)
      ElMessage.success('已安全登出')
    }
  }

  const loginUrl = (nextUrl = window.location.pathname + window.location.search + window.location.hash) => {
    return authApi.loginUrl(nextUrl || '/')
  }
  
  const loginWithCasdoor = (nextUrl) => {
    window.location.href = loginUrl(nextUrl)
  }

  const toggleView = () => {
    if (user.value?.role !== 'admin') return
    viewMode.value = viewMode.value === 'admin' ? 'user' : 'admin'
    localStorage.setItem(VIEW_KEY, viewMode.value)
  }

  const updateProfile = async (data) => {
    const res = await authApi.updateProfile(data)
    user.value = res.data
    return res.data
  }

  return {
    user,
    isInitialized,
    isLoading,
    viewMode,
    isAuthenticated,
    isAdmin,
    effectiveRole,
    isAdminView,
    fetchUser,
    logout,
    loginUrl,
    loginWithCasdoor,
    toggleView,
    updateProfile
  }
})
