<template>
  <el-header class="header glass-card">
    <div class="header-content">
      <div class="logo" @click="navigate('home')">
        <el-icon size="28" color="var(--primary-color)"><Search /></el-icon>
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
          <el-menu-item index="admin" @click="navigate('admin')">
            <el-icon><Setting /></el-icon> 管理
          </el-menu-item>
        </el-menu>
        
        <div class="nav-actions">
          <el-button type="primary" size="large" round class="publish-btn" @click="navigate('create')">
            <el-icon><Plus /></el-icon> 发布寻物/招领
          </el-button>
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
           <el-button type="primary" size="large" round class="publish-btn full-width" @click="navigate('create'); drawerVisible = false">
            <el-icon><Plus /></el-icon> 发布寻物/招领
          </el-button>
        </div>
      </div>
    </el-drawer>
  </el-header>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Search, HomeFilled, Document, Plus, Setting, Menu } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

const activeMenu = computed(() => route.name || 'home')
const drawerVisible = ref(false)

const navItems = [
  { key: 'home', label: '首页', icon: HomeFilled },
  { key: 'lost', label: '发现', icon: Document },
  { key: 'admin', label: '管理后台', icon: Setting },
]

const navigate = (name) => {
  router.push({ name })
}
</script>

<style scoped>
.header {
  position: sticky;
  top: 0;
  z-index: 100;
  padding: 0 20px;
  height: var(--header-height);
  border-radius: 0;
  border-left: none;
  border-right: none;
  border-top: none;
  box-shadow: 0 4px 20px rgba(0,0,0,0.03);
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
  transition: transform 0.3s ease;
}

.logo:hover {
  transform: scale(1.02);
}

.logo-text {
  font-size: 22px;
  font-weight: 800;
  background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
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
  transition: all 0.3s ease;
  height: var(--header-height);
  line-height: var(--header-height);
}

.nav-menu :deep(.el-menu-item:hover),
.nav-menu :deep(.el-menu-item.is-active) {
  background: transparent;
  color: var(--primary-color);
}

.nav-menu :deep(.el-menu-item.is-active) {
  border-bottom-color: var(--primary-color);
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.publish-btn {
  font-weight: 600;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4);
  transition: transform 0.2s, box-shadow 0.2s;
}

.publish-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.6);
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
  background: rgba(99, 102, 241, 0.1);
  color: var(--primary-color);
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
