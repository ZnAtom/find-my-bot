<template>
  <div class="lost-list-page">
    <!-- 搜索栏 -->
    <div class="search-bar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索失物名称、描述、地点…"
        prefix-icon="Search"
        class="search-input"
        @keyup.enter="handleSearch"
      />
      <div class="search-filters">
        <el-select v-model="filterType" placeholder="类型" class="filter-select">
          <el-option label="全部类型" value="" />
          <el-option label="电子产品" value="电子产品" />
          <el-option label="证件卡片" value="证件卡片" />
          <el-option label="衣物鞋帽" value="衣物鞋帽" />
          <el-option label="学习用品" value="学习用品" />
          <el-option label="其他" value="其他" />
        </el-select>
        <el-select v-model="filterStatus" placeholder="状态" class="filter-select">
          <el-option label="全部状态" value="" />
          <el-option label="丢失" value="lost" />
          <el-option label="已找回" value="found" />
        </el-select>
        <el-radio-group v-model="searchMode" size="small">
          <el-radio-button value="keyword">关键字</el-radio-button>
          <el-radio-button value="semantic">语义</el-radio-button>
        </el-radio-group>
        <el-button type="primary" @click="handleSearch" :loading="loading">搜索</el-button>
      </div>
    </div>

    <!-- 结果提示 -->
    <div v-if="!loading && searchQuery && searched" class="result-hint">
      搜索 "<em>{{ searchQuery }}</em>"，找到 <strong>{{ total }}</strong> 条结果
      <span v-if="searchMode === 'semantic'" class="semantic-badge">语义匹配</span>
    </div>

    <!-- 列表 -->
    <div class="items-grid" v-loading="loading" element-loading-text="搜索中...">
      <el-row :gutter="16">
        <el-col :xs="12" :sm="8" :md="6" :lg="6" v-for="item in items" :key="item.id">
          <el-card class="item-card" shadow="hover" @click="goDetail(item.id)">
            <div v-if="item.similarity !== undefined" class="similarity-badge" :style="{ background: simColor(item.similarity) }">
              {{ (item.similarity * 100).toFixed(0) }}%
            </div>
            <div class="item-image">
              <img v-if="item.image_url" :src="resolveImageUrl(item.image_url.split(',')[0])" alt="" />
              <el-icon v-else size="40" color="#909399"><Picture /></el-icon>
            </div>
            <div class="item-info">
              <div class="item-header">
                <h3 v-html="highlight(item.item_name)"></h3>
                <span :class="['status-tag', item.status]">{{ item.status === 'lost' ? '丢失' : '已找回' }}</span>
              </div>
              <p class="item-type">{{ item.item_type }}</p>
              <p class="item-desc" v-html="highlight(item.description || '')"></p>
              <div class="item-details">
                <div><el-icon><MapLocation /></el-icon><span v-html="highlight(item.location || '')"></span></div>
                <div><el-icon><Clock /></el-icon>{{ formatTime(item.lost_time) }}</div>
              </div>
              <div class="contact-info">
                <div><el-icon><User /></el-icon>{{ item.contact_person }}</div>
                <div v-if="item.contact_phone || item.contact_qq"><el-icon><Phone /></el-icon>{{ item.contact_phone || item.contact_qq }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <el-empty v-if="!loading && total === 0 && searched" description="未找到匹配的失物信息" />

    <div v-if="!loading && total > 0" class="pagination">
      <el-pagination
        :current-page="page" :page-size="pageSize" :total="total"
        layout="total, prev, pager, next"
        small
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Picture, MapLocation, Clock, User, Phone } from '@element-plus/icons-vue'
import { lostItemsApi, resolveImageUrl } from '../api'

const searchQuery = ref('')
const filterType = ref('')
const filterStatus = ref('lost')
const searchMode = ref('keyword')
const items = ref([])
const page = ref(1)
const pageSize = ref(20)
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
    items.value = res.data.items
    total.value = res.data.total
    searched.value = false
  } catch (e) {
    console.error('加载失败', e)
  } finally {
    loading.value = false
  }
}

const handleSearch = async () => {
  if (!searchQuery.value.trim()) {
    loadItems()
    return
  }
  loading.value = true
  searched.value = true
  try {
    if (searchMode.value === 'semantic') {
      const res = await lostItemsApi.semanticSearch({ query: searchQuery.value, limit: 50 })
      items.value = res.data.results
      total.value = res.data.results.length
    } else {
      const res = await lostItemsApi.search({
        query: searchQuery.value,
        item_type: filterType.value || undefined,
        status: filterStatus.value || undefined,
        limit: 50,
      })
      items.value = res.data.results
      total.value = res.data.results.length
    }
  } catch (e) {
    console.error('搜索失败', e)
  } finally {
    loading.value = false
  }
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
    result = result.replace(new RegExp(`(${escapedW})`, 'gi'), '<mark class="highlight">$1</mark>')
  })
  return result
}

const escapeHtml = (str) => {
  const div = document.createElement('div')
  div.textContent = str
  return div.innerHTML
}

const simColor = (s) => { if (s >= 0.8) return '#67C23A'; if (s >= 0.5) return '#E6A23C'; return '#909399' }

const handlePageChange = (p) => { page.value = p; loadItems() }

const formatTime = (t) => t ? new Date(t).toLocaleString('zh-CN') : ''
</script>

<style scoped>
.lost-list-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

/* ===== 搜索栏 ===== */
.search-bar {
  margin-bottom: 16px;
}

.search-input {
  width: 100%;
  max-width: 400px;
  margin-bottom: 10px;
}

.search-filters {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.filter-select {
  width: 130px;
}

.result-hint {
  padding: 8px 14px;
  margin-bottom: 14px;
  background: #ecf5ff;
  border-radius: 6px;
  font-size: 13px;
  color: #606266;
}

.result-hint em { font-style: normal; color: #409EFF; font-weight: 600; }

.semantic-badge {
  display: inline-block;
  margin-left: 6px;
  padding: 1px 8px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  border-radius: 10px;
  font-size: 11px;
}

:deep(.highlight) { background: #fff3cd; color: #856404; padding: 1px 2px; border-radius: 2px; }

/* ===== 卡片网格 ===== */
.items-grid {
  min-height: 200px;
  margin-bottom: 16px;
}

.item-card {
  height: 100%;
  position: relative;
  cursor: pointer;
  transition: transform 0.2s;
  margin-bottom: 16px;
}

.item-card:hover { transform: translateY(-3px); }

.similarity-badge {
  position: absolute;
  top: 6px;
  right: 6px;
  color: #fff;
  font-size: 11px;
  font-weight: bold;
  padding: 2px 7px;
  border-radius: 10px;
  z-index: 1;
}

.item-image {
  height: 110px;
  background: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 10px;
  overflow: hidden;
  border-radius: 4px;
}

.item-image img { width: 100%; height: 100%; object-fit: cover; }

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 4px;
  gap: 4px;
}

.item-header h3 {
  font-size: 14px;
  font-weight: bold;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-tag {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 8px;
  flex-shrink: 0;
}

.status-tag.lost { background: #fef0f0; color: #F56C6C; }
.status-tag.found { background: #f0f9eb; color: #67C23A; }

.item-type { font-size: 11px; color: #409EFF; margin: 0 0 6px; }

.item-desc {
  font-size: 12px;
  color: #606266;
  margin: 0 0 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.item-details { font-size: 11px; color: #909399; margin-bottom: 8px; }
.item-details div { margin-bottom: 2px; display: flex; align-items: center; gap: 2px; }

.contact-info {
  font-size: 11px;
  color: #606266;
  padding-top: 8px;
  border-top: 1px solid #f0f0f0;
}
.contact-info div { margin-bottom: 2px; display: flex; align-items: center; gap: 2px; }

.pagination { display: flex; justify-content: center; }

/* ===== 响应式 ===== */
@media (max-width: 768px) {
  .lost-list-page { padding: 12px; }

  .search-input { max-width: 100%; }

  .search-filters {
    gap: 6px;
  }

  .filter-select {
    width: 110px;
  }

  .item-image { height: 90px; }

  .item-header h3 { font-size: 13px; }
}

@media (max-width: 480px) {
  .search-filters {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-select {
    width: 100%;
  }

  .search-filters :deep(.el-radio-group) {
    justify-content: center;
  }

  .search-filters .el-button {
    width: 100%;
  }
}
</style>
