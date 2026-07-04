<template>
  <el-header class="header">
    <div class="header-content">
      <div class="logo" @click="$emit('navigate', 'home')">
        <el-icon size="32" color="#409EFF"><Search /></el-icon>
        <span class="logo-text">校园失物招领</span>
      </div>
      <el-menu :default-active="activeMenu" mode="horizontal" class="nav-menu">
        <el-menu-item index="home" @click="$emit('navigate', 'home')">
          <el-icon><HomeFilled /></el-icon>
          <span>首页</span>
        </el-menu-item>
        <el-menu-item index="lost" @click="$emit('navigate', 'lost')">
          <el-icon><Document /></el-icon>
          <span>失物列表</span>
        </el-menu-item>
        <el-menu-item index="create" @click="$emit('navigate', 'create')">
          <el-icon><Plus /></el-icon>
          <span>发布信息</span>
        </el-menu-item>
        <el-menu-item index="admin" @click="$emit('navigate', 'admin')">
          <el-icon><Setting /></el-icon>
          <span>管理后台</span>
        </el-menu-item>
      </el-menu>
    </div>
  </el-header>
</template>

<script setup>
import { Search, HomeFilled, Document, Plus, Setting } from '@element-plus/icons-vue'

defineProps({
  activeMenu: {
    type: String,
    default: 'home'
  }
})

defineEmits(['navigate'])
</script>

<style scoped>
.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 0 20px;
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
}

.logo-text {
  font-size: 20px;
  font-weight: bold;
  color: white;
}

.nav-menu {
  background: transparent;
}

.nav-menu :deep(.el-menu-item) {
  color: white;
}

.nav-menu :deep(.el-menu-item.is-active) {
  color: #ffd700;
}
</style>