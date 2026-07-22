<template>
  <div class="lost-list-page">
    <div class="page-shell">
      <header class="list-header">
        <div>
          <p class="page-kicker">Item Library</p>
          <h1 class="page-title">物品库</h1>
          <p class="page-subtitle">按状态、分类和描述检索校园里的寻物与招领记录。</p>
        </div>
      </header>

      <section class="search-console surface-section">
        <div class="search-line">
          <el-input
            v-model="searchQuery"
            size="large"
            class="main-search-input"
            placeholder="输入物品、地点、颜色、品牌或完整描述"
            clearable
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-segmented
            v-model="searchMode"
            :options="searchModeOptions"
            size="large"
            class="mode-segment"
          />
          <el-button type="primary" size="large" round :loading="loading" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
        </div>

        <div class="filter-line">
          <div class="filter-block">
            <span>类型</span>
            <el-segmented v-model="filterDirection" :options="directionOptions" @change="handleFilterChange" />
          </div>
          <div class="filter-block">
            <span>状态</span>
            <el-segmented v-model="filterStatus" :options="statusOptions" @change="handleFilterChange" />
          </div>
          <div class="filter-block">
            <span>分类</span>
            <el-select v-model="filterType" placeholder="全部分类" clearable @change="handleFilterChange" style="width: 110px">
              <el-option v-for="type in itemTypes" :key="type" :label="type" :value="type" />
            </el-select>
          </div>
        </div>
      </section>

      <div v-if="!loading && searched" class="result-summary">
        <div>
          <strong>{{ total }}</strong>
          <span>条结果</span>
          <span v-if="searchQuery">，关键词为“{{ searchQuery }}”</span>
        </div>
        <el-button text @click="resetSearch">清除条件</el-button>
      </div>

      <section class="items-area" v-loading="loading">
        <el-row v-if="items.length > 0" :gutter="18">
          <el-col v-for="item in items" :key="item.id" :xs="24" :sm="12" :lg="6">
            <article class="data-card item-card" @click="goDetail(item.id)">
              <div class="image-frame item-image">
                <img v-if="firstImage(item.image_url)" :src="firstImage(item.image_url)" alt="物品图片" />
                <div v-else class="image-placeholder">
                  <el-icon size="34"><Picture /></el-icon>
                </div>
                <span :class="['status-chip', getStatusClass(item)]">{{ getStatusText(item) }}</span>
              </div>
              <div class="item-body">
                <div class="item-meta">
                  <span class="type-chip">{{ getDirectionText(item.direction) }}</span>
                  <span>{{ formatDate(item.created_at) }}</span>
                </div>
                <h3>
                  <template v-for="(part, index) in highlightParts(item.item_name)" :key="`name-${item.id}-${index}`">
                    <mark v-if="part.mark" class="hl">{{ part.text }}</mark>
                    <span v-else>{{ part.text }}</span>
                  </template>
                </h3>
                <p>
                  <template v-for="(part, index) in highlightParts(item.description || '暂无描述')" :key="`desc-${item.id}-${index}`">
                    <mark v-if="part.mark" class="hl">{{ part.text }}</mark>
                    <span v-else>{{ part.text }}</span>
                  </template>
                </p>
                <div class="item-location">
                  <el-icon><MapLocation /></el-icon>
                  <span>
                    <template v-for="(part, index) in highlightParts(item.location || '未知地点')" :key="`loc-${item.id}-${index}`">
                      <mark v-if="part.mark" class="hl">{{ part.text }}</mark>
                      <span v-else>{{ part.text }}</span>
                    </template>
                  </span>
                </div>

                <div v-if="item.similarity !== undefined" class="score-row">
                  <span>匹配度 {{ (item.similarity * 100).toFixed(0) }}%</span>
                  <el-progress
                    :percentage="item.similarity * 100"
                    :show-text="false"
                    :stroke-width="5"
                    :color="simColor(item.similarity)"
                  />
                </div>
              </div>
            </article>
          </el-col>
        </el-row>

        <div v-else-if="!loading && total === 0" class="empty-panel surface-section">
          <el-empty description="没有找到相关记录">
            <el-button type="primary" round @click="resetSearch">查看全部</el-button>
          </el-empty>
        </div>
      </section>

      <div v-if="!loading && total > pageSize && searchMode !== 'semantic'" class="pagination-row">
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Search, Picture, MapLocation } from '@element-plus/icons-vue'
import { firstSafeImageUrl, lostItemsApi } from '../api'

const searchQuery = ref('')
const filterType = ref('')
const filterStatus = ref('active')
const filterDirection = ref('')
const searchMode = ref('semantic')
const items = ref([])
const allKeywordResults = ref([])
const page = ref(1)
const pageSize = ref(16)
const total = ref(0)
const loading = ref(false)
const searched = ref(false)

const route = useRoute()
const router = useRouter()

const searchModeOptions = [
  { label: '关键字', value: 'keyword' },
  { label: '语义', value: 'semantic' },
]

const statusOptions = [
  { label: '全部', value: '' },
  { label: '进行中', value: 'active' },
  { label: '已找回', value: 'recovered' },
  { label: '已过期', value: 'expired' },
]

const directionOptions = [
  { label: '全部', value: '' },
  { label: '寻物', value: 'lost' },
  { label: '招领', value: 'found' },
]

const itemTypes = ['电子产品', '证件卡片', '衣物鞋帽', '学习用品', '钱包钥匙', '其他']

onMounted(() => {
  const q = route.query.q
  const direction = route.query.direction || route.query.post_type
  if (direction === 'lost' || direction === 'found') {
    filterDirection.value = direction
  }
  if (q) {
    searchQuery.value = q
    handleSearch()
  } else {
    loadItems()
  }
})

const loadItems = async () => {
  loading.value = true
  allKeywordResults.value = []
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (filterType.value) params.item_type = filterType.value
    if (filterStatus.value) params.status = filterStatus.value
    if (filterDirection.value) params.direction = filterDirection.value
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
  if (!searchQuery.value.trim()) {
    page.value = 1
    loadItems()
    return
  }

  loading.value = true
  searched.value = true
  page.value = 1
  try {
    if (searchMode.value === 'semantic' && searchQuery.value.trim()) {
      const res = await lostItemsApi.semanticSearch({
        query: searchQuery.value,
        limit: 10,
        item_type: filterType.value || undefined,
        status: filterStatus.value || undefined,
        direction: filterDirection.value || undefined,
      })
      items.value = res.data.results || []
      total.value = items.value.length
      allKeywordResults.value = []
    } else {
      const res = await lostItemsApi.search({
        query: searchQuery.value || undefined,
        item_type: filterType.value || undefined,
        status: filterStatus.value || undefined,
        direction: filterDirection.value || undefined,
        limit: 200,
      })
      allKeywordResults.value = res.data.results || []
      total.value = allKeywordResults.value.length
      applyKeywordPage()
    }
  } catch (e) {
    console.error('搜索失败', e)
  } finally {
    loading.value = false
  }
}

const applyKeywordPage = () => {
  const start = (page.value - 1) * pageSize.value
  items.value = allKeywordResults.value.slice(start, start + pageSize.value)
}

const handleFilterChange = () => {
  if (searchQuery.value.trim()) {
    handleSearch()
  } else {
    page.value = 1
    loadItems()
  }
}

const resetSearch = () => {
  searchQuery.value = ''
  filterType.value = ''
  filterStatus.value = 'active'
  filterDirection.value = ''
  searchMode.value = 'semantic'
  page.value = 1
  loadItems()
}

const firstImage = (url) => {
  return firstSafeImageUrl(url)
}

const getStatusClass = (item) => {
  if (item.status === 'recovered') return 'recovered'
  if (item.status === 'expired') return 'expired'
  return item.direction === 'lost' ? 'lost' : 'found'
}

const getStatusText = (item) => {
  if (item.status === 'recovered') return '已找回'
  if (item.status === 'expired') return '已过期'
  return item.direction === 'lost' ? '待找回' : '招领中'
}

const getDirectionText = (direction) => direction === 'found' ? '招领' : '寻物'

const goDetail = (id) => {
  router.push({ name: 'detail', params: { id } })
}

const escapeRegExp = (value) => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

const highlightParts = (text) => {
  const value = String(text || '')
  if (!value || !searched.value || searchMode.value === 'semantic') return [{ text: value, mark: false }]
  const q = searchQuery.value.trim()
  if (!q) return [{ text: value, mark: false }]
  const words = q.split(/\s+/).filter(Boolean)
  if (words.length === 0) return [{ text: value, mark: false }]

  const regex = new RegExp(words.map(escapeRegExp).join('|'), 'gi')
  const parts = []
  let lastIndex = 0
  value.replace(regex, (match, offset) => {
    if (offset > lastIndex) {
      parts.push({ text: value.slice(lastIndex, offset), mark: false })
    }
    parts.push({ text: match, mark: true })
    lastIndex = offset + match.length
    return match
  })
  if (lastIndex < value.length) {
    parts.push({ text: value.slice(lastIndex), mark: false })
  }
  return parts.length ? parts : [{ text: value, mark: false }]
}

const simColor = (score) => {
  if (score >= 0.8) return 'var(--success-color)'
  if (score >= 0.5) return 'var(--warning-color)'
  return 'var(--placeholder-icon-color)'
}

const handlePageChange = (nextPage) => {
  page.value = nextPage
  if (searched.value && searchMode.value === 'keyword') {
    applyKeywordPage()
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
.list-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 18px;
  margin-bottom: 22px;
}

.search-console {
  padding: 18px;
  margin-bottom: 18px;
}

.search-line {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  gap: 12px;
  align-items: center;
}

.search-line > * {
  min-width: 0;
}

.main-search-input :deep(.el-input__wrapper) {
  min-height: 46px;
}

.mode-segment {
  min-width: 162px;
}

.filter-line {
  display: flex;
  flex-wrap: wrap;
  gap: 18px;
  align-items: center;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
}

.filter-block {
  display: flex;
  align-items: center;
  gap: 10px;
}

.filter-block > span {
  flex: 0 0 auto;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 800;
  white-space: nowrap;
}

.result-summary {
  min-height: 46px;
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: space-between;
  margin-bottom: 18px;
  padding: 0 4px;
  color: var(--text-secondary);
  font-size: 14px;
}

.result-summary strong {
  color: var(--text-primary);
  font-size: 22px;
}

.result-summary > div {
  flex: 1;
}

.item-card {
  display: flex;
  flex-direction: column;
  margin-bottom: 18px;
}

.item-image {
  height: 178px;
}

.item-image .status-chip {
  position: absolute;
  top: 12px;
  right: 12px;
}

.item-body {
  padding: 16px;
}

.item-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  color: var(--text-tertiary);
  font-size: 12px;
  font-weight: 700;
}

.item-body h3 {
  margin: 13px 0 7px;
  color: var(--text-primary);
  font-size: 17px;
  font-weight: 800;
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.item-body p {
  min-height: 42px;
  margin: 0;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.55;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.item-location {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid var(--border-color);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 700;
}

.score-row {
  margin-top: 12px;
}

.score-row span {
  display: block;
  margin-bottom: 6px;
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 800;
}

.empty-panel {
  padding: 34px;
}

.pagination-row {
  display: flex;
  justify-content: center;
  margin-top: 10px;
}

@media (max-width: 900px) {
  .list-header {
    flex-direction: column;
  }

  .search-line {
    grid-template-columns: 1fr;
  }

  .mode-segment {
    width: 100%;
  }
}

@media (max-width: 640px) {
  .filter-block {
    width: 100%;
    align-items: flex-start;
    flex-direction: column;
  }

  .filter-block :deep(.el-segmented),
  .filter-block :deep(.el-select) {
    width: 100%;
  }

  .result-summary {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
