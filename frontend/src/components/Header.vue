<template>
  <el-header class="header glass-card">
    <div class="header-content">
      <div class="logo" @click="navigate('home')">
        <el-icon size="28" color="var(--brand-primary)"><Search /></el-icon>
        <span class="logo-text">校园失物招领</span>
      </div>

      <!-- 桌面端菜单 -->
      <div class="desktop-nav">
        <el-menu :default-active="activeMenu" mode="horizontal" class="nav-menu" :ellipsis="false">
          <el-menu-item index="home" @click="navigate('home')">
            <el-icon><HomeFilled /></el-icon> 首页
          </el-menu-item>
          <el-menu-item index="lost" @click="navigate('lost')">
            <el-icon><Document /></el-icon> 发现
          </el-menu-item>
          <el-menu-item v-if="userStore.isAdminView" index="admin" @click="navigate('admin')">
            <el-icon><Setting /></el-icon> 管理
          </el-menu-item>
        </el-menu>
        
        <div class="nav-actions">
          <el-button v-if="userStore.isAuthenticated" type="primary" size="large" round class="publish-btn" @click="navigate('create')">
            <el-icon><Plus /></el-icon> 发布寻物/招领
          </el-button>
          <el-button v-else type="primary" size="large" round class="publish-btn" @click="userStore.loginWithCasdoor()">
            <el-icon><User /></el-icon> 登录
          </el-button>
          <el-dropdown v-if="userStore.isAuthenticated" trigger="click">
            <el-button text class="user-menu-btn">
              <el-icon><User /></el-icon>
              <span>{{ userStore.user?.name || userStore.user?.student_id || '已登录' }}</span>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="navigate('profile')">
                  <el-icon><User /></el-icon>
                  个人中心
                </el-dropdown-item>
                <el-dropdown-item v-if="userStore.isAdmin" @click="userStore.toggleView()">
                  <el-icon><Switch /></el-icon>
                  切换到{{ userStore.isAdminView ? '普通用户预览' : '管理员视角' }}
                </el-dropdown-item>
                <el-dropdown-item divided @click="logout">
                  <el-icon><SwitchButton /></el-icon> 退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>

      <!-- 手机端汉堡按钮 -->
      <el-button class="mobile-menu-btn" text @click="drawerVisible = true">
        <el-icon size="24" color="var(--text-primary)"><Menu /></el-icon>
      </el-button>
    </div>

    <!-- 手机端抽屉菜单 -->
    <el-drawer
      v-model="drawerVisible"
      direction="rtl"
      size="70%"
      :with-header="false"
      class="mobile-drawer"
    >
      <div class="drawer-nav">
        <div class="drawer-title">校园失物招领</div>
        <div
          v-for="item in navItems"
          :key="item.key"
          :class="['drawer-item', { active: activeMenu === item.key }]"
          @click="navigate(item.key); drawerVisible = false"
        >
          <el-icon size="20" class="drawer-icon"><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </div>
        <div class="drawer-action">
          <el-button v-if="userStore.isAuthenticated" type="primary" size="large" round class="publish-btn full-width" @click="navigate('create'); drawerVisible = false">
            <el-icon><Plus /></el-icon> 发布寻物/招领
          </el-button>
          <el-button v-else type="primary" size="large" round class="publish-btn full-width" @click="userStore.loginWithCasdoor(); drawerVisible = false">
            <el-icon><User /></el-icon> 登录
          </el-button>
          <el-button v-if="userStore.isAuthenticated" size="large" round class="full-width logout-btn" @click="logout(); drawerVisible = false">
            <el-icon><SwitchButton /></el-icon> 退出登录
          </el-button>
        </div>
      </div>
    </el-drawer>
  </el-header>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Search, HomeFilled, Document, Plus, Setting, Menu, User, SwitchButton, Switch } from '@element-plus/icons-vue'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()

const router = useRouter()
const route = useRoute()

const activeMenu = computed(() => route.name || 'home')
const drawerVisible = ref(false)

const navItems = computed(() => [
  { key: 'home', label: '首页', icon: HomeFilled },
  { key: 'lost', label: '发现', icon: Document },
  ...(userStore.isAuthenticated ? [{ key: 'profile', label: '个人中心', icon: User }] : []),
  ...(userStore.isAdminView ? [{ key: 'admin', label: '管理后台', icon: Setting }] : []),
])

const navigate = (name) => {
  router.push({ name })
}

const logout = async () => {
  await userStore.logout()
  if (route.meta.requiresAuth) {
    router.push({ name: 'home' })
  }
}
</script>

<style scoped>
.header {
  position: sticky;
  top: 0;
  z-index: 100;
  padding: 0 20px;
  height: var(--header-height);
  background: var(--card-bg);
  border-bottom: 1px solid var(--border-color);
  box-shadow: var(--card-shadow);
  transition: all 0.2s ease;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  max-width: 1200px;
  margin: 0 auto;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  flex-shrink: 0;
  transition: opacity 0.2s ease;
}

.logo:hover {
  opacity: 0.8;
}

.logo-text {
  font-size: 20px;
  font-weight: 700;
  color: var(--brand-primary);
  letter-spacing: -0.5px;
}

/* 桌面菜单 */
.desktop-nav {
  display: flex;
  align-items: center;
  flex-grow: 1;
  justify-content: space-between;
  margin-left: 40px;
}

.nav-menu {
  background: transparent;
  border-bottom: none !important;
  flex-grow: 1;
}

.nav-menu :deep(.el-menu-item) {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-secondary);
  border-bottom: 2px solid transparent;
  transition: all 0.2s ease;
  height: var(--header-height);
  line-height: var(--header-height);
}

.nav-menu :deep(.el-menu-item:hover),
.nav-menu :deep(.el-menu-item.is-active) {
  background: transparent;
  color: var(--brand-primary);
}

.nav-menu :deep(.el-menu-item.is-active) {
  border-bottom-color: var(--brand-primary);
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-menu-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--text-secondary);
  font-weight: 600;
}

.publish-btn {
  font-weight: 600;
}

/* 手机菜单按钮 */
.mobile-menu-btn {
  display: none;
}

/* 抽屉菜单 */
.drawer-nav {
  padding: 30px 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.drawer-title {
  font-size: 20px;
  font-weight: 800;
  color: var(--text-primary);
  margin-bottom: 30px;
}

.drawer-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  font-size: 16px;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: var(--border-radius-md);
  transition: all 0.2s;
  margin-bottom: 8px;
}

.drawer-item:hover,
.drawer-item.active {
  background: rgba(124, 58, 237, 0.08);
  color: var(--brand-primary);
}

.drawer-icon {
  transition: transform 0.2s;
}
.drawer-item:hover .drawer-icon {
  transform: scale(1.1);
}

.drawer-action {
  margin-top: auto;
  padding-top: 20px;
}

.full-width {
  width: 100%;
}

.logout-btn {
  margin-top: 12px;
}

/* ===== 响应式 ===== */
@media (max-width: 768px) {
  .desktop-nav {
    display: none;
  }

  .mobile-menu-btn {
    display: flex;
  }

  .logo-text {
    font-size: 18px;
  }
}
</style>
