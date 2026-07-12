<template>
  <div class="home-page">
    <div class="page-shell">
      <section class="workbench">
        <div class="search-card surface-section">
          <p class="page-kicker">FoundIt Campus</p>
          <h1 class="page-title">找回物品，从一条清楚的记录开始。</h1>
          <p class="page-subtitle">搜索物品、地点、颜色或完整描述。需要发布时，选择寻物或招领即可进入对应流程。</p>

          <div class="search-panel">
            <el-input
              v-model="searchQuery"
              size="large"
              placeholder="二教黑色耳机，或图书馆校园卡"
              clearable
              @keyup.enter="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-button type="primary" size="large" round @click="handleSearch">
              搜索
            </el-button>
          </div>
        </div>

        <div class="action-stack">
          <button class="action-card lost" type="button" @click="goCreate('lost')">
            <el-icon><Warning /></el-icon>
            <span>
              <strong>我丢了东西</strong>
              <small>发布寻物记录</small>
            </span>
          </button>
          <button class="action-card found" type="button" @click="goCreate('found')">
            <el-icon><CircleCheck /></el-icon>
            <span>
              <strong>我捡到东西</strong>
              <small>发布招领记录</small>
            </span>
          </button>
          <button class="action-card neutral" type="button" @click="router.push({ name: 'lost' })">
            <el-icon><Collection /></el-icon>
            <span>
              <strong>浏览物品库</strong>
              <small>查看全部公开记录</small>
            </span>
          </button>
        </div>
      </section>

      <section class="review-grid">
        <div class="surface-section list-panel">
          <div class="panel-heading">
            <div>
              <p class="page-kicker">Lost</p>
              <h2>正在寻找</h2>
            </div>
            <el-button text @click="router.push({ name: 'lost', query: { direction: 'lost' } })">
              查看全部
            </el-button>
          </div>

          <el-skeleton v-if="loading" animated :rows="4" />
          <div v-else-if="lostItems.length" class="compact-list">
            <button v-for="item in lostItems" :key="item.id" class="compact-item" type="button" @click="goDetail(item.id)">
              <span class="thumb">
                <img v-if="firstImage(item.image_url)" :src="resolveImageUrl(firstImage(item.image_url))" alt="" />
                <el-icon v-else><Picture /></el-icon>
              </span>
              <span class="compact-copy">
                <strong>{{ item.item_name }}</strong>
                <small>{{ item.location || '未知地点' }} · {{ formatDate(item.created_at) }}</small>
              </span>
              <span class="status-chip lost">待找回</span>
            </button>
          </div>
          <el-empty v-else description="暂无寻物记录" />
        </div>

        <div class="surface-section list-panel">
          <div class="panel-heading">
            <div>
              <p class="page-kicker">Found</p>
              <h2>等待认领</h2>
            </div>
            <el-button text @click="router.push({ name: 'lost', query: { direction: 'found' } })">
              查看全部
            </el-button>
          </div>

          <el-skeleton v-if="loading" animated :rows="4" />
          <div v-else-if="foundItems.length" class="compact-list">
            <button v-for="item in foundItems" :key="item.id" class="compact-item" type="button" @click="goDetail(item.id)">
              <span class="thumb">
                <img v-if="firstImage(item.image_url)" :src="resolveImageUrl(firstImage(item.image_url))" alt="" />
                <el-icon v-else><Picture /></el-icon>
              </span>
              <span class="compact-copy">
                <strong>{{ item.item_name }}</strong>
                <small>{{ item.location || '未知地点' }} · {{ formatDate(item.created_at) }}</small>
              </span>
              <span class="status-chip found">招领中</span>
            </button>
          </div>
          <el-empty v-else description="暂无招领记录" />
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { CircleCheck, Collection, Picture, Search, Warning } from '@element-plus/icons-vue'
import { lostItemsApi, resolveImageUrl } from '../api'

const searchQuery = ref('')
const lostItems = ref([])
const foundItems = ref([])
const loading = ref(true)
const router = useRouter()

onMounted(() => {
  loadLatestItems()
})

const loadLatestItems = async () => {
  loading.value = true
  try {
    const [lostRes, foundRes] = await Promise.all([
      lostItemsApi.getAll({ page: 1, page_size: 5, status: 'active', direction: 'lost' }, { silent: true }),
      lostItemsApi.getAll({ page: 1, page_size: 5, status: 'active', direction: 'found' }, { silent: true }),
    ])
    lostItems.value = lostRes.data.items || []
    foundItems.value = foundRes.data.items || []
  } catch (e) {
    console.error('加载最新记录失败', e)
  } finally {
    loading.value = false
  }
}

const firstImage = (url) => {
  if (!url) return ''
  return url.split(',').map(v => v.trim()).filter(Boolean)[0] || ''
}

const goDetail = (id) => {
  router.push({ name: 'detail', params: { id } })
}

const goCreate = (postType) => {
  router.push({ name: 'create', query: { type: postType } })
}

const handleSearch = () => {
  if (searchQuery.value.trim()) {
    router.push({ name: 'lost', query: { q: searchQuery.value.trim() } })
  } else {
    router.push({ name: 'lost' })
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}月${date.getDate()}日`
}
</script>

<style scoped>
.workbench {
  display: grid;
  grid-template-columns: 1fr;
  gap: 18px;
  align-items: stretch;
}

.workbench > * {
  min-width: 0;
}

.search-card {
  padding: 34px;
}

.search-panel {
  margin-top: 30px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  padding: 10px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  background: var(--surface-muted);
}

.search-panel > * {
  min-width: 0;
}

.search-panel :deep(.el-input__wrapper) {
  min-height: 46px;
  background: transparent;
  box-shadow: none !important;
}

.action-stack {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.action-card {
  min-height: 112px;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 20px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  background: var(--surface-color);
  color: var(--text-primary);
  text-align: left;
  box-shadow: var(--card-shadow);
  cursor: pointer;
}

.action-card:hover {
  border-color: var(--border-strong);
  box-shadow: var(--card-hover-shadow);
}

.action-card .el-icon {
  width: 42px;
  height: 42px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 22px;
  flex: 0 0 auto;
}

.action-card.lost .el-icon {
  color: #991b1b;
  background: #fee2e2;
}

.action-card.found .el-icon {
  color: #0f766e;
  background: #ccfbf1;
}

.action-card.neutral .el-icon {
  color: var(--foundit-blue);
  background: rgba(37, 99, 235, 0.1);
}

.action-card strong,
.action-card small {
  display: block;
}

.action-card strong {
  font-size: 16px;
  font-weight: 800;
}

.action-card small {
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 13px;
}

.review-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
  margin-top: 18px;
}

.list-panel {
  padding: 18px;
}

.panel-heading {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: flex-start;
  margin-bottom: 14px;
}

.panel-heading h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 800;
}

.compact-list {
  display: grid;
  gap: 10px;
}

.compact-item {
  width: 100%;
  display: grid;
  grid-template-columns: 52px minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
  padding: 10px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  background: var(--surface-color);
  text-align: left;
  cursor: pointer;
}

.compact-item:hover {
  border-color: var(--border-strong);
}

.thumb {
  width: 52px;
  height: 52px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: var(--border-radius-md);
  background: var(--surface-muted);
  color: #94a3b8;
}

.thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.compact-copy {
  min-width: 0;
}

.compact-copy strong,
.compact-copy small {
  display: block;
}

.compact-copy strong {
  overflow: hidden;
  color: var(--text-primary);
  font-size: 15px;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.compact-copy small {
  margin-top: 4px;
  overflow: hidden;
  color: var(--text-secondary);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (min-width: 921px) {
  .workbench {
    grid-template-columns: minmax(0, 1fr) 310px;
  }

  .action-stack {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 920px) {
  .review-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .search-card {
    padding: 22px;
  }

  .search-card .page-title {
    font-size: 28px;
    line-height: 1.12;
    word-break: auto-phrase;
  }

  .search-card .page-subtitle {
    font-size: 15px;
  }

  .search-panel {
    margin-top: 24px;
    grid-template-columns: 1fr;
  }

  .search-panel :deep(.el-button) {
    width: 100%;
  }

  .action-stack {
    grid-template-columns: 1fr;
  }

  .compact-item {
    grid-template-columns: 48px minmax(0, 1fr);
  }

  .compact-item .status-chip {
    grid-column: 2;
    justify-self: start;
  }
}
</style>
