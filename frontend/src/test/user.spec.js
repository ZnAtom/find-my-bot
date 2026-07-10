import { setActivePinia, createPinia } from 'pinia'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useUserStore } from '../stores/user'
import { authApi } from '../api'

// Mock API
vi.mock('../api', () => ({
  authApi: {
    me: vi.fn(),
    logout: vi.fn(),
    loginUrl: vi.fn((url) => `/api/auth/login?next=${url}`),
    updateProfile: vi.fn()
  }
}))

describe('User Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('initializes with default state', () => {
    const store = useUserStore()
    expect(store.user).toBeNull()
    expect(store.isInitialized).toBe(false)
    expect(store.isLoading).toBe(false)
    expect(store.viewMode).toBe('user')
    expect(store.isAuthenticated).toBe(false)
    expect(store.isAdmin).toBe(false)
  })

  it('fetches user successfully', async () => {
    const store = useUserStore()
    const mockUser = { id: 1, name: 'Test User', role: 'user' }
    authApi.me.mockResolvedValueOnce({ data: { user: mockUser } })

    await store.fetchUser()

    expect(store.user).toEqual(mockUser)
    expect(store.isInitialized).toBe(true)
    expect(store.isAuthenticated).toBe(true)
    expect(store.isAdmin).toBe(false)
  })

  it('handles fetch user error', async () => {
    const store = useUserStore()
    authApi.me.mockRejectedValueOnce(new Error('Network error'))

    await store.fetchUser()

    expect(store.user).toBeNull()
    expect(store.isInitialized).toBe(true)
    expect(store.isAuthenticated).toBe(false)
  })

  it('toggles view mode for admin', async () => {
    const store = useUserStore()
    store.user = { id: 1, name: 'Admin', role: 'admin' }
    
    store.toggleView()
    expect(store.viewMode).toBe('admin')
    expect(store.isAdminView).toBe(true)

    store.toggleView()
    expect(store.viewMode).toBe('user')
    expect(store.isAdminView).toBe(false)
  })

  it('logout clears user state', async () => {
    const store = useUserStore()
    store.user = { id: 1, name: 'Test User' }
    authApi.logout.mockResolvedValueOnce({})

    await store.logout()

    expect(store.user).toBeNull()
    expect(store.isAuthenticated).toBe(false)
    expect(store.viewMode).toBe('user')
  })
})
