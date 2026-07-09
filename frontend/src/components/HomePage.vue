<template>
  <div class="home-page">
    <!-- Hero -->
    <div class="hero-section">
      <div class="hero-content">
        <h1>校园失物招领平台</h1>
        <p>智能匹配 · 快速找回 · 服务师生</p>
        <div class="search-box">
          <el-input
            v-model="searchQuery"
            placeholder="搜索失物…"
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

    <!-- 最新失物 -->
    <div class="content-section">
      <div class="section-header">
        <h2>最新失物信息</h2>
        <el-button type="text" @click="router.push({ name: 'lost' })">查看全部 →</el-button>
      </div>

      <!-- 加载骨架 -->
      <el-row :gutter="20" v-if="loading">
        <el-col :xs="12" :sm="12" :md="6" v-for="i in 4" :key="i">
          <el-card class="item-card">
            <el-skeleton animated>
              <template #template>
                <el-skeleton-item variant="image" style="width:100%;height:120px" />
                <div style="padding:12px">
                  <el-skeleton-item variant="text" style="width:60%" />
                  <el-skeleton-item variant="text" style="width:30%;margin-top:6px" />
                  <el-skeleton-item variant="text" style="width:80%;margin-top:6px" />
                </div>
              </template>
            </el-skeleton>
          </el-card>
        </el-col>
      </el-row>

      <!-- 内容 -->
      <el-row :gutter="20" v-else>
        <el-col :xs="12" :sm="12" :md="6" v-for="item in latestItems" :key="item.id">
          <el-card class="item-card" shadow="hover" @click="goDetail(item.id)">
            <div class="item-image">
              <img v-if="item.image_url" :src="resolveImageUrl(item.image_url.split(',')[0])" alt="物品图片" />
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

      <el-empty v-if="!loading && latestItems.length === 0" description="还没有失物信息，去发布一条吧" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Box, HelpFilled, CircleCheck, User, Picture, MapLocation } from '@element-plus/icons-vue'
import { lostItemsApi, statsApi, resolveImageUrl } from '../api'

const searchQuery = ref('')
const stats = ref({})
const latestItems = ref([])
const loading = ref(true)
const router = useRouter()

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
  loading.value = true
  try {
    const res = await lostItemsApi.getAll({ page: 1, page_size: 4, status: 'lost' })
    latestItems.value = res.data.items || []
  } catch (e) {
    console.error('加载最新失物失败', e)
  } finally {
    loading.value = false
  }
}

const goDetail = (id) => {
  router.push({ name: 'detail', params: { id } })
}

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

/* ===== Hero ===== */
.hero-section {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 80px 0;
  text-align: center;
}

.hero-content h1 {
  font-size: 48px;
  color: white;
  margin: 0 0 16px;
}

.hero-content > p {
  font-size: 20px;
  color: rgba(255,255,255,0.8);
  margin-bottom: 40px;
}

.search-box {
  display: flex;
  justify-content: center;
  gap: 10px;
  max-width: 600px;
  margin: 0 auto;
  padding: 0 20px;
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

/* ===== 内容区 ===== */
.content-section {
  padding: 40px;
  max-width: 1200px;
  margin: 0 auto;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.section-header h2 {
  font-size: 22px;
  font-weight: bold;
  margin: 0;
}

/* ===== 卡片 ===== */
.item-card {
  height: 100%;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  margin-bottom: 20px;
}

.item-card:hover {
  transform: translateY(-4px);
}

.item-image {
  height: 120px;
  background: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
  overflow: hidden;
  border-radius: 4px;
}

.item-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.item-info h3 {
  font-size: 15px;
  font-weight: bold;
  margin: 0 0 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-type {
  font-size: 12px;
  color: #409EFF;
  margin: 0 0 6px;
}

.item-desc {
  font-size: 13px;
  color: #606266;
  margin: 0 0 10px;
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
  display: flex;
  align-items: center;
  gap: 2px;
}

.status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 10px;
}

.status.lost { background: #fef0f0; color: #F56C6C; }
.status.found { background: #f0f9eb; color: #67C23A; }

/* ===== 响应式 ===== */
@media (max-width: 768px) {
  .hero-section {
    padding: 40px 16px;
  }

  .hero-content h1 {
    font-size: 26px;
    margin-bottom: 8px;
  }

  .hero-content > p {
    font-size: 14px;
    margin-bottom: 24px;
  }

  .search-box {
    flex-direction: column;
    gap: 8px;
    padding: 0;
  }

  .search-box :deep(.el-input__wrapper) {
    border-radius: 25px;
  }

  .search-box :deep(.el-button) {
    border-radius: 25px;
    width: 100%;
  }

  .quick-stats {
    gap: 24px;
    margin-top: 32px;
    flex-wrap: wrap;
  }

  .stat-value {
    font-size: 24px;
  }

  .stat-label {
    font-size: 12px;
  }

  .content-section {
    padding: 20px 12px;
  }

  .section-header h2 {
    font-size: 18px;
  }

  .item-image {
    height: 100px;
  }
}
</style>
