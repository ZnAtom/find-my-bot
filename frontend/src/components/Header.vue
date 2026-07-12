<template>
  <el-header class="app-header">
    <div class="header-inner">
      <button class="brand-button" type="button" @click="navigate('home')" aria-label="FoundIt 首页">
        <img class="brand-logo" :src="logoUrl" alt="FoundIt" />
      </button>

      <nav class="desktop-nav" aria-label="主导航">
        <button
          v-for="item in desktopItems"
          :key="item.key"
          :class="['nav-link', { active: activeKey === item.key }]"
          type="button"
          @click="navigate(item.key)"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </button>
      </nav>

      <div class="header-actions">
        <el-button
          v-if="userStore.isAuthenticated"
          type="primary"
          round
          @click="navigate('create')"
        >
          <el-icon><Plus /></el-icon>
          发布
        </el-button>
        <el-button
          v-else
          type="primary"
          round
          @click="userStore.loginWithCasdoor()"
        >
          <el-icon><User /></el-icon>
          登录
        </el-button>

        <el-popover
          v-if="userStore.isAuthenticated"
          placement="bottom-end"
          width="340"
          trigger="click"
          @show="loadNotifications"
        >
          <template #reference>
            <el-badge :value="unreadCount" :hidden="unreadCount === 0" :max="99">
              <button class="notification-button" type="button" aria-label="系统通知">
                <el-icon><Bell /></el-icon>
              </button>
            </el-badge>
          </template>
          <div class="notification-panel">
            <div class="notification-title">系统通知</div>
            <div v-if="notificationsLoading" class="notification-empty">加载中...</div>
            <div v-else-if="notifications.length === 0" class="notification-empty">暂无通知</div>
            <button
              v-for="notice in notifications"
              v-else
              :key="notice.id"
              :class="['notification-item', { unread: !notice.is_read }]"
              type="button"
              @click="openNotification(notice)"
            >
              <strong>{{ notice.title }}</strong>
              <span>{{ notice.message || '无详细内容' }}</span>
              <small>{{ formatNoticeTime(notice.created_at) }}</small>
            </button>
          </div>
        </el-popover>

        <button
          class="theme-toggle-button"
          type="button"
          :aria-label="themeToggleLabel"
          :title="themeToggleLabel"
          @click="toggleTheme"
        >
          <el-icon><component :is="isDarkTheme ? Sunny : Moon" /></el-icon>
        </button>

        <el-dropdown v-if="userStore.isAuthenticated" trigger="click">
          <button class="account-button" type="button">
            <span class="avatar-dot">{{ userInitial }}</span>
            <span class="account-name">{{ userStore.user?.name || userStore.user?.student_id || '已登录' }}</span>
          </button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="navigate('profile')">
                <el-icon><User /></el-icon>
                个人中心
              </el-dropdown-item>
              <el-dropdown-item v-if="userStore.isAdmin" @click="userStore.toggleView()">
                <el-icon><Switch /></el-icon>
                {{ userStore.isAdminView ? '普通用户模式' : '管理员模式' }}
              </el-dropdown-item>
              <el-dropdown-item divided @click="logout">
                <el-icon><SwitchButton /></el-icon>
                退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <el-button class="mobile-menu-button" text @click="drawerVisible = true" aria-label="打开导航">
          <el-icon size="22"><Menu /></el-icon>
        </el-button>
      </div>
    </div>

    <el-drawer
      v-model="drawerVisible"
      direction="rtl"
      size="82%"
      :with-header="false"
      append-to-body
      :z-index="3000"
      class="mobile-drawer"
    >
      <div class="drawer-shell">
        <div class="drawer-brand">
          <div class="drawer-avatar">{{ userInitial }}</div>
          <div>
            <strong>{{ userStore.user?.name || userStore.user?.student_id || '未登录' }}</strong>
            <span>{{ userStore.isAuthenticated ? userStore.user?.student_id || '已登录' : '登录后管理发布和通知' }}</span>
          </div>
        </div>

        <button
          v-for="item in mobileItems"
          :key="item.key"
          :class="['drawer-link', { active: activeKey === item.key }]"
          type="button"
          @click="navigateFromDrawer(item.key)"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </button>

        <div class="drawer-footer">
          <el-button
            v-if="userStore.isAuthenticated"
            type="primary"
            round
            class="full-width"
            @click="navigateFromDrawer('create')"
          >
            <el-icon><Plus /></el-icon>
            发布寻物或招领
          </el-button>
          <el-button
            v-else
            type="primary"
            round
            class="full-width"
            @click="userStore.loginWithCasdoor(); drawerVisible = false"
          >
            <el-icon><User /></el-icon>
            登录 FoundIt
          </el-button>
          <el-button
            v-if="userStore.isAuthenticated"
            round
            class="full-width"
            @click="logout(); drawerVisible = false"
          >
            <el-icon><SwitchButton /></el-icon>
            退出登录
          </el-button>
        </div>
      </div>
    </el-drawer>
  </el-header>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Collection,
  Bell,
  HomeFilled,
  Menu,
  Moon,
  Plus,
  Setting,
  Sunny,
  Switch,
  SwitchButton,
  User,
} from '@element-plus/icons-vue'
import { useUserStore } from '../stores/user'
import { notificationsApi } from '../api'
import { theme, toggleTheme } from '../theme'
import logoUrl from '../assets/foundit-logo.svg'

const userStore = useUserStore()
const router = useRouter()
const route = useRoute()
const drawerVisible = ref(false)
const notifications = ref([])
const unreadCount = ref(0)
const notificationsLoading = ref(false)

const activeKey = computed(() => {
  if (route.name === 'detail') return 'lost'
  return route.name || 'home'
})

const baseItems = computed(() => [
  { key: 'home', label: '首页', icon: HomeFilled },
  { key: 'lost', label: '物品库', icon: Collection },
  ...(userStore.isAuthenticated ? [{ key: 'profile', label: '个人中心', icon: User }] : []),
  ...(userStore.isAdminView ? [{ key: 'admin', label: '管理', icon: Setting }] : []),
])

const desktopItems = computed(() => baseItems.value)
const mobileItems = computed(() => baseItems.value)
const isDarkTheme = computed(() => theme.value === 'dark')
const themeToggleLabel = computed(() => isDarkTheme.value ? '切换到亮色模式' : '切换到黑暗模式')

const userInitial = computed(() => {
  const name = userStore.user?.name || userStore.user?.student_id || 'F'
  return String(name).slice(0, 1).toUpperCase()
})

const navigate = (name) => {
  router.push({ name })
}

const navigateFromDrawer = (name) => {
  drawerVisible.value = false
  navigate(name)
}

const loadUnreadCount = async () => {
  if (!userStore.isAuthenticated) {
    unreadCount.value = 0
    return
  }
  try {
    const res = await notificationsApi.unreadCount()
    unreadCount.value = res.data.unread_count || 0
  } catch {
    unreadCount.value = 0
  }
}

const loadNotifications = async () => {
  if (!userStore.isAuthenticated) return
  notificationsLoading.value = true
  try {
    const res = await notificationsApi.list({ limit: 20 })
    notifications.value = res.data || []
    await loadUnreadCount()
  } catch {
    notifications.value = []
    unreadCount.value = 0
  } finally {
    notificationsLoading.value = false
  }
}

const openNotification = async (notice) => {
  if (!notice.is_read) {
    try {
      await notificationsApi.markRead(notice.id)
      notice.is_read = true
      await loadUnreadCount()
    } catch {
      // Do not block navigation when marking read fails.
    }
  }
  if (notice.link_url) {
    router.push(notice.link_url)
  } else if (notice.related_item_id) {
    router.push({ name: 'detail', params: { id: notice.related_item_id } })
  }
}

const formatNoticeTime = (value) => {
  if (!value) return ''
  return new Date(value).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

const logout = async () => {
  await userStore.logout()
  notifications.value = []
  unreadCount.value = 0
  if (route.meta.requiresAuth) {
    router.push({ name: 'home' })
  }
}

watch(() => userStore.isAuthenticated, (isAuthed) => {
  if (isAuthed) {
    loadUnreadCount()
  } else {
    notifications.value = []
    unreadCount.value = 0
  }
})

onMounted(loadUnreadCount)
</script>

<style scoped>
.app-header {
  position: sticky;
  top: 0;
  z-index: 100;
  height: var(--header-height);
  padding: 0;
  border-bottom: 1px solid var(--header-border);
  background: var(--header-bg);
  backdrop-filter: blur(16px);
}

.header-inner {
  width: calc(100% - 40px);
  max-width: var(--page-max-width);
  height: 100%;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 24px;
}

.brand-button {
  width: 168px;
  height: 42px;
  display: inline-flex;
  align-items: center;
  border: 0;
  padding: 0;
  background: transparent;
  cursor: pointer;
}

.brand-logo {
  width: 168px;
  height: auto;
  display: block;
}

.desktop-nav {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
}

.nav-link {
  height: 40px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 0 14px;
  border: 1px solid transparent;
  border-radius: 999px;
  background: transparent;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
}

.nav-link:hover,
.nav-link.active {
  color: var(--foundit-blue);
  background: var(--accent-soft-hover);
  border-color: var(--accent-soft-border);
}

.header-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 10px;
}

.account-button {
  height: 38px;
  display: inline-flex;
  align-items: center;
  gap: 9px;
  max-width: 190px;
  padding: 0 11px 0 5px;
  border: 1px solid var(--border-color);
  border-radius: 999px;
  background: var(--surface-color);
  color: var(--text-primary);
  cursor: pointer;
}

.avatar-dot {
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--foundit-blue), var(--foundit-teal));
  color: #fff;
  font-size: 12px;
  font-weight: 800;
}

.account-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  font-weight: 700;
}

.notification-button,
.theme-toggle-button {
  width: 38px;
  height: 38px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border-color);
  border-radius: 999px;
  background: var(--surface-color);
  color: var(--text-secondary);
  cursor: pointer;
}

.notification-button:hover,
.theme-toggle-button:hover {
  color: var(--foundit-blue);
  border-color: var(--accent-soft-border);
  background: var(--accent-soft-hover);
}

.notification-panel {
  max-height: 420px;
  overflow-y: auto;
}

.notification-title {
  padding: 4px 2px 10px;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-primary);
  font-weight: 800;
}

.notification-empty {
  padding: 28px 0;
  text-align: center;
  color: var(--text-secondary);
}

.notification-item {
  width: 100%;
  display: grid;
  gap: 4px;
  padding: 12px 4px;
  border: 0;
  border-bottom: 1px solid var(--border-color);
  background: transparent;
  color: var(--text-primary);
  text-align: left;
  cursor: pointer;
}

.notification-item:hover {
  background: var(--surface-color);
}

.notification-item strong {
  font-size: 14px;
}

.notification-item span {
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.5;
}

.notification-item small {
  color: var(--text-secondary);
  font-size: 12px;
}

.notification-item.unread strong::before {
  content: '';
  width: 7px;
  height: 7px;
  display: inline-block;
  margin-right: 6px;
  border-radius: 50%;
  background: var(--foundit-blue);
  vertical-align: middle;
}

.mobile-menu-button {
  display: none;
}

.drawer-shell {
  min-height: 100%;
  padding: 22px;
  display: flex;
  flex-direction: column;
}

.drawer-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 22px;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 18px;
}

.drawer-avatar {
  width: 44px;
  height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--foundit-blue), var(--foundit-teal));
  color: #fff;
  font-size: 16px;
  font-weight: 800;
}

.drawer-brand strong,
.drawer-brand > div > span {
  display: block;
}

.drawer-brand strong {
  font-size: 18px;
}

.drawer-brand > div > span {
  margin-top: 2px;
  color: var(--text-secondary);
  font-size: 13px;
}

.drawer-link {
  width: 100%;
  height: 48px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 14px;
  border: 1px solid transparent;
  border-radius: var(--border-radius-lg);
  background: transparent;
  color: var(--text-secondary);
  font-size: 15px;
  font-weight: 700;
  text-align: left;
  cursor: pointer;
}

.drawer-link.active {
  color: var(--foundit-blue);
  background: var(--accent-soft-hover);
  border-color: var(--accent-soft-border);
}

.drawer-footer {
  margin-top: auto;
  display: grid;
  gap: 10px;
}

.full-width {
  width: 100%;
}

:deep(.mobile-drawer) {
  z-index: 3001;
}

:deep(.mobile-drawer.el-drawer) {
  position: fixed;
}

@media (max-width: 860px) {
  .header-inner {
    width: calc(100% - 28px);
  }

  .brand-button,
  .brand-logo {
    width: 140px;
  }

  .desktop-nav,
  .account-button,
  .header-actions > .el-button:not(.mobile-menu-button) {
    display: none;
  }

  .mobile-menu-button {
    display: inline-flex;
  }
}
</style>
