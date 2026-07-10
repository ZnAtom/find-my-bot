<template>
  <div class="home-page">
    <!-- Hero -->
    <div class="hero-section">
      <div class="hero-bg-animated"></div>
      <div class="hero-content">
        <h1 class="hero-title">校园失物招领平台</h1>
        <p class="hero-subtitle">智能匹配 · 快速找回 · 服务师生</p>
        <div class="search-box glass-card">
          <el-input
            v-model="searchQuery"
            placeholder="搜索失物、招领信息…"
            size="large"
            @keyup.enter="handleSearch"
            class="search-input"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-button type="primary" size="large" round @click="handleSearch" class="search-btn">
            全站搜索
          </el-button>
        </div>
        <div class="quick-stats">
          <div class="stat-card glass-card">
            <el-icon size="28" color="var(--brand-primary)"><Box /></el-icon>
            <div class="stat-info">
              <span class="stat-value">{{ stats.total_items || 0 }}</span>
              <span class="stat-label">总失物</span>
            </div>
          </div>
          <div class="stat-card glass-card">
            <el-icon size="28" color="var(--danger-color)"><HelpFilled /></el-icon>
            <div class="stat-info">
              <span class="stat-value">{{ stats.lost_count || 0 }}</span>
              <span class="stat-label">待找回</span>
            </div>
          </div>
          <div class="stat-card glass-card">
            <el-icon size="28" color="var(--success-color)"><CircleCheck /></el-icon>
            <div class="stat-info">
              <span class="stat-value">{{ stats.found_count || 0 }}</span>
              <span class="stat-label">已找回</span>
            </div>
          </div>
          <div class="stat-card glass-card">
            <el-icon size="28" color="var(--warning-color)"><User /></el-icon>
            <div class="stat-info">
              <span class="stat-value">{{ stats.user_count || 0 }}</span>
              <span class="stat-label">用户数</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 最新失物 -->
    <div class="content-section">
      <div class="section-header">
        <div class="title-group">
          <h2>最新动态</h2>
          <p class="subtitle">实时更新的失物与招领信息</p>
        </div>
        <el-button round class="view-all-btn" @click="router.push({ name: 'lost' })">
          浏览全部 <el-icon class="el-icon--right"><ArrowRight /></el-icon>
        </el-button>
      </div>

      <!-- 加载骨架 -->
      <el-row :gutter="24" v-if="loading">
        <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="i in 4" :key="i">
          <el-card class="modern-card skeleton-card" shadow="never">
            <el-skeleton animated>
              <template #template>
                <el-skeleton-item variant="image" class="card-img-skeleton" />
                <div style="padding:16px">
                  <el-skeleton-item variant="text" style="width:60%; height:20px" />
                  <el-skeleton-item variant="text" style="width:40%; margin-top:12px" />
                  <el-skeleton-item variant="text" style="width:90%; margin-top:12px" />
                </div>
              </template>
            </el-skeleton>
          </el-card>
        </el-col>
      </el-row>

      <!-- 内容 -->
      <el-row :gutter="24" v-else-if="latestItems.length > 0">
        <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="item in latestItems" :key="item.id">
          <div class="modern-card" @click="goDetail(item.id)">
            <div class="card-image-wrapper">
              <img v-if="item.image_url" :src="resolveImageUrl(item.image_url.split(',')[0])" alt="物品图片" class="card-img" />
              <div v-else class="card-img-placeholder">
                <el-icon size="48" color="#c0c4cc"><Picture /></el-icon>
              </div>
              <div :class="['status-badge', getStatusClass(item)]">
                {{ getStatusText(item) }}
              </div>
            </div>
            <div class="card-content">
              <div class="card-meta">
                <span class="item-type">{{ item.item_type || '未分类' }}</span>
                <span class="time-ago">{{ formatDate(item.created_at) }}</span>
              </div>
              <h3 class="card-title">{{ item.item_name }}</h3>
              <p class="card-desc">{{ item.description || '无详细描述' }}</p>
              <div class="card-footer">
                <span class="location">
                  <el-icon><MapLocation /></el-icon> {{ item.location || '未知地点' }}
                </span>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>

      <div v-else class="empty-state glass-card">
        <el-empty description="暂时还没有失物信息哦，去发布第一条吧！">
          <el-button type="primary" round size="large" @click="router.push({ name: 'create' })">立即发布</el-button>
        </el-empty>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search, Box, HelpFilled, CircleCheck, User, Picture, MapLocation, ArrowRight } from '@element-plus/icons-vue'
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
    const res = await lostItemsApi.getAll({ page: 1, page_size: 4 })
    latestItems.value = res.data.items || []
  } catch (e) {
    console.error('加载最新失物失败', e)
  } finally {
    loading.value = false
  }
}

const getStatusClass = (item) => {
  if (item.status === 'found') return 'resolved'
  return item.status === 'lost' ? 'lost' : 'found'
}

const getStatusText = (item) => {
  if (item.status === 'found') return '已找回'
  return item.status === 'lost' ? '待找回' : '招领'
}

const goDetail = (id) => {
  router.push({ name: 'detail', params: { id } })
}

const handleSearch = () => {
  if (searchQuery.value.trim()) {
    router.push({ name: 'lost', query: { q: searchQuery.value.trim() } })
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}月${date.getDate()}日`
}
</script>

<style scoped>
.home-page {
  min-height: calc(100vh - var(--header-height));
}

/* ===== Hero ===== */
.hero-section {
  position: relative;
  padding: 100px 0 120px;
  text-align: center;
  background: transparent;
}

.hero-bg-animated {
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle at 50% 50%, rgba(99, 102, 241, 0.15) 0%, rgba(236, 72, 153, 0.05) 50%, transparent 100%);
  animation: rotateBg 30s linear infinite;
  z-index: 0;
}

@keyframes rotateBg {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.hero-content {
  position: relative;
  z-index: 1;
  max-width: 1000px;
  margin: 0 auto;
  padding: 0 20px;
}

.hero-title {
  font-size: 56px;
  font-weight: 800;
  letter-spacing: -1px;
  color: var(--text-primary);
  margin-bottom: 16px;
  background: linear-gradient(135deg, var(--text-primary) 0%, #475569 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.hero-subtitle {
  font-size: 22px;
  color: var(--text-secondary);
  margin-bottom: 48px;
  font-weight: 400;
}

.search-box {
  display: flex;
  align-items: center;
  max-width: 680px;
  margin: 0 auto;
  padding: 8px 8px 8px 24px;
  border-radius: 50px;
  background: var(--surface-color);
  box-shadow: 0 20px 40px rgba(0,0,0,0.05);
}

.search-input :deep(.el-input__wrapper) {
  box-shadow: none !important;
  background: transparent;
  padding: 0;
  font-size: 16px;
}

.search-btn {
  padding: 12px 32px;
  font-size: 16px;
  font-weight: 600;
}

.quick-stats {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin-top: 80px;
  flex-wrap: wrap;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 32px;
  background: var(--glass-bg);
  backdrop-filter: blur(12px);
  border: 1px solid var(--glass-border);
  border-radius: var(--border-radius-lg);
  min-width: 200px;
  box-shadow: var(--glass-shadow);
  transition: all 0.4s var(--spring-easing);
}

.stat-card:hover {
  transform: translateY(-8px) scale(1.02);
  box-shadow: 0 15px 30px rgba(124, 58, 237, 0.1);
  background: var(--glass-hover-bg);
}

.stat-info {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 500;
}

/* ===== 内容区 ===== */
.content-section {
  padding: 60px 20px 100px;
  max-width: 1200px;
  margin: 0 auto;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 40px;
}

.title-group h2 {
  font-size: 32px;
  font-weight: 800;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.title-group .subtitle {
  font-size: 16px;
  color: var(--text-secondary);
}

.view-all-btn {
  font-weight: 600;
}

/* ===== 现代卡片 ===== */
.modern-card {
  background: var(--glass-bg);
  backdrop-filter: blur(12px);
  border-radius: var(--border-radius-lg);
  overflow: hidden;
  cursor: pointer;
  transition: all 0.4s var(--spring-easing);
  box-shadow: var(--glass-shadow);
  border: 1px solid var(--glass-border);
  height: 100%;
  display: flex;
  flex-direction: column;
  margin-bottom: 24px;
}

.modern-card:hover {
  transform: translateY(-10px);
  box-shadow: 0 20px 40px rgba(31, 38, 135, 0.1);
  background: var(--glass-hover-bg);
}

.card-image-wrapper {
  position: relative;
  height: 200px;
  overflow: hidden;
  background: #f1f5f9;
}

.card-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s ease;
}

.modern-card:hover .card-img {
  transform: scale(1.05);
}

.card-img-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-badge {
  position: absolute;
  top: 16px;
  right: 16px;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 700;
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.status-badge.lost {
  background: rgba(239, 68, 68, 0.9);
  color: white;
}

.status-badge.found {
  background: rgba(16, 185, 129, 0.9);
  color: white;
}

.status-badge.resolved {
  background: rgba(107, 114, 128, 0.9);
  color: white;
}

.card-content {
  padding: 24px;
  display: flex;
  flex-direction: column;
  flex-grow: 1;
}

.card-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.item-type {
  font-size: 13px;
  font-weight: 600;
  color: var(--brand-primary);
  background: rgba(124, 58, 237, 0.1);
  padding: 4px 10px;
  border-radius: 6px;
}

.time-ago {
  font-size: 13px;
  color: var(--text-secondary);
}

.card-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-desc {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 20px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  flex-grow: 1;
}

.card-footer {
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
}

.location {
  font-size: 13px;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 6px;
}

.skeleton-card {
  padding: 0;
}

.card-img-skeleton {
  width: 100%;
  height: 200px;
}

.empty-state {
  padding: 60px 20px;
  border-radius: var(--border-radius-lg);
  text-align: center;
}

/* ===== 响应式 ===== */
@media (max-width: 768px) {
  .hero-section {
    padding: 60px 0 80px;
  }

  .hero-title {
    font-size: 36px;
  }

  .hero-subtitle {
    font-size: 16px;
  }

  .search-box {
    padding: 6px 6px 6px 16px;
  }

  .search-btn {
    padding: 10px 24px;
  }

  .quick-stats {
    gap: 16px;
    margin-top: 40px;
  }

  .stat-card {
    min-width: 140px;
    padding: 16px;
  }

  .stat-value {
    font-size: 24px;
  }

  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
}
</style>
