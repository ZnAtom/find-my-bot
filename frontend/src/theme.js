import { ref } from 'vue'

const STORAGE_KEY = 'foundit-theme'
const DARK_QUERY = '(prefers-color-scheme: dark)'

export const theme = ref('light')

let listenerAttached = false

const normalizeTheme = (value) => value === 'dark' ? 'dark' : 'light'

const readStoredTheme = () => {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY)
    return stored === 'dark' || stored === 'light' ? stored : null
  } catch {
    return null
  }
}

const systemTheme = () => {
  if (typeof window === 'undefined' || !window.matchMedia) return 'light'
  return window.matchMedia(DARK_QUERY).matches ? 'dark' : 'light'
}

const applyTheme = (nextTheme) => {
  const normalized = normalizeTheme(nextTheme)
  theme.value = normalized

  if (typeof document === 'undefined') return

  const root = document.documentElement
  root.classList.toggle('dark', normalized === 'dark')
  root.dataset.theme = normalized
  root.style.colorScheme = normalized
}

export const initTheme = () => {
  applyTheme(readStoredTheme() || systemTheme())

  if (!listenerAttached && typeof window !== 'undefined' && window.matchMedia) {
    const mediaQuery = window.matchMedia(DARK_QUERY)
    const handleSystemChange = (event) => {
      if (!readStoredTheme()) {
        applyTheme(event.matches ? 'dark' : 'light')
      }
    }

    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleSystemChange)
    } else if (mediaQuery.addListener) {
      mediaQuery.addListener(handleSystemChange)
    }
    listenerAttached = true
  }
}

export const setTheme = (nextTheme) => {
  const normalized = normalizeTheme(nextTheme)
  try {
    window.localStorage.setItem(STORAGE_KEY, normalized)
  } catch {
    // Theme still applies for the current session when storage is unavailable.
  }
  applyTheme(normalized)
}

export const toggleTheme = () => {
  setTheme(theme.value === 'dark' ? 'light' : 'dark')
}
