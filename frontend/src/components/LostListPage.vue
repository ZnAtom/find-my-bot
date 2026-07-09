<template>
  <div class="lost-list-page">
    <div class="page-header">
      <h1 class="page-title">发现</h1>
      <p class="page-subtitle">在这里浏览最新的失物与招领信息，或使用 AI 语义检索快速定位。</p>
    </div>

    <!-- 搜索与过滤面板 -->
    <div class="filter-panel glass-card">
      <div class="search-row">
        <el-input
          v-model="searchQuery"
          placeholder="试试输入：“昨天在图书馆丢的黑色小米手机”"
          size="large"
          class="main-search-input"
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-radio-group v-model="searchMode" size="large" class="mode-toggle">
          <el-radio-button value="keyword"><el-icon><Filter /></el-icon> 关键字</el-radio-button>
          <el-radio-button value="semantic"><el-icon><MagicStick /></el-icon> AI语义</el-radio-button>
        </el-radio-group>
        <el-button type="primary" size="large" @click="handleSearch" :loading="loading" class="search-btn" round>
          搜索
        </el-button>
      </div>

      <div class="filter-row">
        <div class="filter-group">
          <span class="filter-label">状态:</span>
          <el-radio-group v-model="filterStatus" @change="handleFilterChange">
            <el-radio-button value="">全部</el-radio-button>
            <el-radio-button value="lost">🔍 丢失</el-radio-button>
            <el-radio-button value="found">✅ 找回</el-radio-button>
          </el-radio-group>
        </div>
        
        <div class="filter-group">
          <span class="filter-label">分类:</span>
          <el-select v-model="filterType" placeholder="全部分类" style="width: 140px" @change="handleFilterChange">
            <el-option label="全部" value="" />
            <el-option label="电子产品" value="电子产品" />
            <el-option label="证件卡片" value="证件卡片" />
            <el-option label="衣物鞋帽" value="衣物鞋帽" />
            <el-option label="学习用品" value="学习用品" />
            <el-option label="钱包钥匙" value="钱包钥匙" />
            <el-option label="其他" value="其他" />
          </el-select>
        </div>
      </div>
    </div>

    <!-- 结果提示 -->
    <div v-if="!loading && searchQuery && searched" class="result-hint">
      <el-icon><InfoFilled /></el-icon>
      为您找到关于 <span class="highlight-text">"{{ searchQuery }}"</span> 的 <strong>{{ total }}</strong> 条记录
      <el-tag v-if="searchMode === 'semantic'" effect="dark" round size="small" class="semantic-tag">
        <el-icon><MagicStick /></el-icon> 语义匹配
      </el-tag>
    </div>

    <!-- 列表 -->
    <div class="items-container" v-loading="loading">
      <el-row :gutter="24" v-if="items.length > 0">
        <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="item in items" :key="item.id">
          <div class="modern-card" @click="goDetail(item.id)">
            <div class="card-image-wrapper">
              <img v-if="item.image_url" :src="resolveImageUrl(item.image_url.split(',')[0])" alt="" class="card-img" />
              <div v-else class="card-img-placeholder">
                <el-icon size="48" color="#cbd5e1"><Picture /></el-icon>
              </div>
              <div :class="['status-badge', item.status]">
                {{ item.status === 'lost' ? '待找回' : '已找回' }}
              </div>
            </div>
            
            <div class="card-content">
              <div class="card-meta">
                <span class="item-type">{{ item.item_type || '未分类' }}</span>
                <span class="time-ago">{{ formatDate(item.created_at) }}</span>
              </div>
              
              <h3 class="card-title" v-html="highlight(item.item_name)"></h3>
              <p class="card-desc" v-html="highlight(item.description || '暂无描述')"></p>
              
              <div class="card-footer">
                <span class="location">
                  <el-icon><MapLocation /></el-icon> <span v-html="highlight(item.location || '未知地点')"></span>
                </span>
              </div>

              <!-- 匹配度进度条 (仅语义搜索时显示) -->
              <div v-if="item.similarity !== undefined" class="sim-score-box">
                <div class="score-label">匹配度 {{ (item.similarity * 100).toFixed(0) }}%</div>
                <el-progress 
                  :percentage="item.similarity * 100" 
                  :show-text="false" 
                  :color="simColor(item.similarity)" 
                  :stroke-width="4" 
                />
              </div>
            </div>
          </div>
        </el-col>
      </el-row>

      <div v-else-if="!loading && total === 0" class="empty-state glass-card">
        <el-empty description="没有找到相关的物品信息">
          <el-button type="primary" round @click="resetSearch">清除搜索条件</el-button>
        </el-empty>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="!loading && total > pageSize" class="pagination-container">
      <el-pagination
        background
        :current-page="page" 
        :page-size="pageSize" 
        :total="total"
        layout="prev, pager, next"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Search, Filter, MagicStick, Picture, MapLocation, InfoFilled } from '@element-plus/icons-vue'
import { lostItemsApi, resolveImageUrl } from '../api'

const searchQuery = ref('')
const filterType = ref('')
const filterStatus = ref('')
const searchMode = ref('keyword')
const items = ref([])
const page = ref(1)
const pageSize = ref(16)
const total = ref(0)
const loading = ref(false)
const searched = ref(false)

const route = useRoute()
const router = useRouter()

onMounted(() => {
  const q = route.query.q
  if (q) {
    searchQuery.value = q
    handleSearch()
  } else {
    loadItems()
  }
})

const loadItems = async () => {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (filterType.value) params.item_type = filterType.value
    if (filterStatus.value) params.status = filterStatus.value
    const res = await lostItemsApi.getAll(params)
    items.value = res.data.items || []
    total.value = res.data.total || 0
    searched.value = false
  } catch (e) {
    console.error('加载失败', e)
  } finally {
    loading.value = false
  }
}

const handleSearch = async () => {
  if (!searchQuery.value.trim() && !filterType.value && !filterStatus.value) {
    loadItems()
    return
  }
  loading.value = true
  searched.value = true
  page.value = 1
  try {
    if (searchMode.value === 'semantic' && searchQuery.value.trim()) {
      const res = await lostItemsApi.semanticSearch({ query: searchQuery.value, limit: pageSize.value })
      items.value = res.data.results || []
      total.value = res.data.results?.length || 0
    } else {
      const res = await lostItemsApi.search({
        query: searchQuery.value || undefined,
        item_type: filterType.value || undefined,
        status: filterStatus.value || undefined,
        limit: 100, // 关键字搜索目前后端未做分页，前端获取尽量多的然后截断
      })
      // 简单前端分页处理
      const allResults = res.data.results || []
      total.value = allResults.length
      items.value = allResults.slice(0, pageSize.value)
    }
  } catch (e) {
    console.error('搜索失败', e)
  } finally {
    loading.value = false
  }
}

const handleFilterChange = () => {
  if (searchQuery.value.trim() || filterType.value || filterStatus.value) {
    handleSearch()
  } else {
    loadItems()
  }
}

const resetSearch = () => {
  searchQuery.value = ''
  filterType.value = ''
  filterStatus.value = ''
  loadItems()
}

const goDetail = (id) => { router.push({ name: 'detail', params: { id } }) }

const highlight = (text) => {
  if (!text || !searched.value || searchMode.value === 'semantic') return escapeHtml(text || '')
  const q = searchQuery.value.trim()
  if (!q) return escapeHtml(text)
  const escaped = escapeHtml(text)
  const words = q.split(/\s+/).filter(Boolean)
  let result = escaped
  words.forEach(w => {
    const escapedW = w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    result = result.replace(new RegExp(`(${escapedW})`, 'gi'), '<mark class="hl">$1</mark>')
  })
  return result
}

const escapeHtml = (str) => {
  const div = document.createElement('div')
  div.textContent = str
  return div.innerHTML
}

const simColor = (s) => { 
  if (s >= 0.8) return 'var(--success-color)'
  if (s >= 0.5) return 'var(--warning-color)'
  return '#94a3b8' 
}

const handlePageChange = (p) => { 
  page.value = p
  if (searched.value && searchMode.value === 'keyword') {
    // keyword search fake pagination handled above if needed, but standard loadItems otherwise
    // to keep it simple, just load items if not semantic (since semantic has no pagination yet)
  } else {
    loadItems()
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}月${date.getDate()}日`
}
</script>

<style scoped>
.lost-list-page {
  padding: 40px 20px;
  max-width: 1200px;
  margin: 0 auto;
  min-height: calc(100vh - var(--header-height));
}

.page-header {
  text-align: center;
  margin-bottom: 32px;
}
.page-title {
  font-size: 32px;
  font-weight: 800;
  color: var(--text-primary);
  margin-bottom: 8px;
}
.page-subtitle {
  color: var(--text-secondary);
  font-size: 16px;
}

/* 过滤面板 */
.filter-panel {
  padding: 24px;
  margin-bottom: 32px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.search-row {
  display: flex;
  gap: 16px;
  align-items: center;
}

.main-search-input {
  flex-grow: 1;
}
.main-search-input :deep(.el-input__wrapper) {
  border-radius: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.search-btn {
  padding: 0 32px;
  font-weight: 600;
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
  align-items: center;
  padding-top: 20px;
  border-top: 1px solid var(--border-color);
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 12px;
}
.filter-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
}

.result-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: var(--surface-color);
  border-radius: var(--border-radius-md);
  margin-bottom: 24px;
  color: var(--text-secondary);
  font-size: 14px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.02);
}
.highlight-text {
  color: var(--primary-color);
  font-weight: 700;
}
.result-hint strong {
  color: var(--text-primary);
  font-size: 16px;
}
.semantic-tag {
  background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
  border: none;
}

:deep(.hl) { 
  background: rgba(245, 158, 11, 0.2); 
  color: #b45309; 
  padding: 0 2px; 
  border-radius: 2px; 
}

/* 卡片样式 (复用现代卡片) */
.modern-card {
  background: var(--surface-color);
  border-radius: var(--border-radius-lg);
  overflow: hidden;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
  box-shadow: 0 4px 20px rgba(0,0,0,0.03);
  border: 1px solid var(--border-color);
  height: 100%;
  display: flex;
  flex-direction: column;
  margin-bottom: 24px;
}

.modern-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 16px 32px rgba(0,0,0,0.08);
  border-color: transparent;
}

.card-image-wrapper {
  position: relative;
  height: 180px;
  background: #f1f5f9;
  overflow: hidden;
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
  top: 12px;
  right: 12px;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 700;
  backdrop-filter: blur(8px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.status-badge.lost { background: rgba(239, 68, 68, 0.9); color: white; }
.status-badge.found { background: rgba(16, 185, 129, 0.9); color: white; }

.card-content {
  padding: 20px;
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
  font-size: 12px;
  font-weight: 600;
  color: var(--primary-color);
  background: rgba(99, 102, 241, 0.1);
  padding: 4px 8px;
  border-radius: 6px;
}
.time-ago {
  font-size: 12px;
  color: var(--text-secondary);
}

.card-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-desc {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: 16px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  flex-grow: 1;
}

.card-footer {
  padding-top: 12px;
  border-top: 1px solid var(--border-color);
  margin-bottom: 8px;
}

.location {
  font-size: 12px;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 4px;
}

.sim-score-box {
  margin-top: 12px;
}
.score-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.empty-state {
  padding: 60px;
  text-align: center;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 40px;
}

/* 响应式 */
@media (max-width: 768px) {
  .lost-list-page {
    padding: 20px 16px;
  }
  .search-row {
    flex-direction: column;
    align-items: stretch;
  }
  .search-btn {
    width: 100%;
  }
  .mode-toggle {
    display: flex;
  }
  .mode-toggle :deep(.el-radio-button) {
    flex: 1;
  }
  .mode-toggle :deep(.el-radio-button__inner) {
    width: 100%;
  }
  .filter-row {
    flex-direction: column;
    align-items: flex-start;
  }
  .card-image-wrapper {
    height: 140px;
  }
}
</style>
