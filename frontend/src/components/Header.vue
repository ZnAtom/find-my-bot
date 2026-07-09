<template>
  <el-header class="header">
    <div class="header-content">
      <div class="logo" @click="navigate('home')">
        <el-icon size="28" color="#409EFF"><Search /></el-icon>
        <span class="logo-text">校园失物招领</span>
      </div>

      <!-- 桌面端菜单 -->
      <el-menu :default-active="activeMenu" mode="horizontal" class="nav-menu desktop-nav">
        <el-menu-item index="home" @click="navigate('home')">
          <el-icon><HomeFilled /></el-icon>
          <span>首页</span>
        </el-menu-item>
        <el-menu-item index="lost" @click="navigate('lost')">
          <el-icon><Document /></el-icon>
          <span>失物列表</span>
        </el-menu-item>
        <el-menu-item index="create" @click="navigate('create')">
          <el-icon><Plus /></el-icon>
          <span>发布信息</span>
        </el-menu-item>
        <el-menu-item index="admin" @click="navigate('admin')">
          <el-icon><Setting /></el-icon>
          <span>管理后台</span>
        </el-menu-item>
      </el-menu>

      <!-- 手机端汉堡按钮 -->
      <el-button class="mobile-menu-btn" text @click="drawerVisible = true">
        <el-icon size="24" color="#fff"><Menu /></el-icon>
      </el-button>
    </div>

    <!-- 手机端抽屉菜单 -->
    <el-drawer
      v-model="drawerVisible"
      direction="rtl"
      size="70%"
      :with-header="false"
    >
      <div class="drawer-nav">
        <div class="drawer-title">校园失物招领</div>
        <div
          v-for="item in navItems"
          :key="item.key"
          :class="['drawer-item', { active: activeMenu === item.key }]"
          @click="navigate(item.key); drawerVisible = false"
        >
          <el-icon size="20"><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
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
  { key: 'lost', label: '失物列表', icon: Document },
  { key: 'create', label: '发布信息', icon: Plus },
  { key: 'admin', label: '管理后台', icon: Setting },
]

const navigate = (name) => {
  router.push({ name })
}
</script>

<style scoped>
.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 0 20px;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 60px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  flex-shrink: 0;
}

.logo-text {
  font-size: 20px;
  font-weight: bold;
  color: white;
}

/* 桌面菜单 */
.nav-menu {
  background: transparent;
  border-bottom: none !important;
}

.nav-menu :deep(.el-menu-item) {
  color: rgba(255, 255, 255, 0.85);
  border-bottom: 2px solid transparent;
}

.nav-menu :deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.nav-menu :deep(.el-menu-item.is-active) {
  color: #ffd700;
  border-bottom-color: #ffd700;
}

/* 手机菜单按钮 */
.mobile-menu-btn {
  display: none;
}

/* 抽屉菜单 */
.drawer-nav {
  padding: 20px 0;
}

.drawer-title {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
  padding: 0 20px 16px;
  border-bottom: 1px solid #ebeef5;
  margin-bottom: 8px;
}

.drawer-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  font-size: 16px;
  color: #303133;
  cursor: pointer;
  transition: background 0.2s;
}

.drawer-item:hover,
.drawer-item.active {
  background: #ecf5ff;
  color: #409EFF;
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
    font-size: 16px;
  }
}
</style>
