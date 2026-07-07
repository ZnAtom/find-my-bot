<template>
  <div class="home-page">
    <div class="hero-section">
      <div class="hero-content">
        <h1>校园失物招领平台</h1>
        <p>智能匹配 · 快速找回 · 服务师生</p>
        <div class="search-box">
          <el-input
            v-model="searchQuery"
            placeholder="搜索失物信息，如：手机、钱包、校园卡..."
            prefix-icon="Search"
            size="large"
            @keyup.enter="handleSearch"
          />
          <el-button type="primary" size="large" @click="handleSearch">搜索</el-button>
        </div>
        <div class="quick-stats">
          <div class="stat-item">
            <el-icon size="24" color="#409EFF"><Box /></el-icon>
            <span class="stat-value">{{ stats.total_items || 0 }}</span>
            <span class="stat-label">总失物</span>
          </div>
          <div class="stat-item">
            <el-icon size="24" color="#F56C6C"><HelpFilled /></el-icon>
            <span class="stat-value">{{ stats.lost_count || 0 }}</span>
            <span class="stat-label">待找回</span>
          </div>
          <div class="stat-item">
            <el-icon size="24" color="#67C23A"><CircleCheck /></el-icon>
            <span class="stat-value">{{ stats.found_count || 0 }}</span>
            <span class="stat-label">已找回</span>
          </div>
          <div class="stat-item">
            <el-icon size="24" color="#E6A23C"><User /></el-icon>
            <span class="stat-value">{{ stats.user_count || 0 }}</span>
            <span class="stat-label">用户数</span>
          </div>
        </div>
      </div>
    </div>

    <div class="content-section">
      <div class="section-header">
        <h2>最新失物信息</h2>
        <el-button type="text" @click="router.push({ name: 'lost' })">查看全部</el-button>
      </div>
      <el-row :gutter="20">
        <el-col :span="6" v-for="item in latestItems" :key="item.id">
          <el-card class="item-card">
            <div class="item-image">
              <img v-if="item.image_url" :src="item.image_url.split(',')[0]" alt="物品图片" />
              <el-icon v-else size="48" color="#909399"><Picture /></el-icon>
            </div>
            <div class="item-info">
              <h3>{{ item.item_name }}</h3>
              <p class="item-type">{{ item.item_type }}</p>
              <p class="item-desc">{{ item.description }}</p>
              <div class="item-meta">
                <span class="location"><el-icon><MapLocation /></el-icon>{{ item.location }}</span>
                <span :class="['status', item.status]">{{ item.status === 'lost' ? '丢失' : '已找回' }}</span>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Box, HelpFilled, CircleCheck, User, Picture, MapLocation } from '@element-plus/icons-vue'
import { lostItemsApi, statsApi } from '../api'

const searchQuery = ref('')
const stats = ref({})
const latestItems = ref([])

onMounted(() => {
  loadStats()
  loadLatestItems()
})

const loadStats = async () => {
  try {
    const res = await statsApi.get()
    stats.value = res.data
  } catch (e) {
    console.error('加载统计数据失败', e)
  }
}

const loadLatestItems = async () => {
  try {
    const res = await lostItemsApi.getAll({ page: 1, page_size: 4 })
    latestItems.value = res.data.items || []
  } catch (e) {
    console.error('加载最新失物失败', e)
  }
}

const router = useRouter()

const handleSearch = () => {
  if (searchQuery.value.trim()) {
    router.push({ name: 'lost', query: { q: searchQuery.value.trim() } })
  }
}
</script>

<style scoped>
.home-page {
  min-height: calc(100vh - 60px);
}

.hero-section {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 80px 0;
  text-align: center;
}

.hero-content h1 {
  font-size: 48px;
  color: white;
  margin-bottom: 16px;
}

.hero-content p {
  font-size: 20px;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 40px;
}

.search-box {
  display: flex;
  justify-content: center;
  gap: 10px;
  max-width: 600px;
  margin: 0 auto;
}

.search-box :deep(.el-input__wrapper) {
  border-radius: 25px 0 0 25px;
}

.search-box :deep(.el-button) {
  border-radius: 0 25px 25px 0;
}

.quick-stats {
  display: flex;
  justify-content: center;
  gap: 60px;
  margin-top: 60px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: white;
}

.stat-value {
  font-size: 36px;
  font-weight: bold;
  margin: 10px 0;
}

.stat-label {
  font-size: 14px;
  opacity: 0.8;
}

.content-section {
  padding: 60px 40px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.section-header h2 {
  font-size: 24px;
  font-weight: bold;
}

.item-card {
  height: 100%;
}

.item-image {
  height: 120px;
  background: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 15px;
  overflow: hidden;
}

.item-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.item-info h3 {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 5px;
}

.item-type {
  font-size: 12px;
  color: #409EFF;
  margin-bottom: 8px;
}

.item-desc {
  font-size: 13px;
  color: #606266;
  margin-bottom: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.item-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.location {
  font-size: 12px;
  color: #909399;
}

.status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 10px;
}

.status.lost {
  background: #fef0f0;
  color: #F56C6C;
}

.status.found {
  background: #f0f9eb;
  color: #67C23A;
}
</style>