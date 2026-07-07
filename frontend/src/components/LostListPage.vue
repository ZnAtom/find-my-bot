<template>
  <div class="lost-list-page">
    <div class="search-bar">
      <el-input 
        v-model="searchQuery" 
        placeholder="搜索失物名称、描述、地点..." 
        prefix-icon="Search"
        style="width: 300px;"
        @keyup.enter="handleSearch"
      />
      <el-select v-model="filterType" placeholder="物品类型" style="width: 150px; margin-left: 10px;">
        <el-option label="全部" value="" />
        <el-option label="电子产品" value="电子产品" />
        <el-option label="证件卡片" value="证件卡片" />
        <el-option label="衣物鞋帽" value="衣物鞋帽" />
        <el-option label="学习用品" value="学习用品" />
        <el-option label="其他" value="其他" />
      </el-select>
      <el-select v-model="filterStatus" placeholder="状态" style="width: 120px; margin-left: 10px;">
        <el-option label="全部" value="" />
        <el-option label="丢失" value="lost" />
        <el-option label="已找回" value="found" />
      </el-select>
      <el-button type="primary" @click="handleSearch">搜索</el-button>
    </div>

    <div class="items-grid">
      <el-row :gutter="20">
        <el-col :span="6" v-for="item in items" :key="item.id">
          <el-card class="item-card">
            <div class="item-image">
              <el-icon size="48" color="#909399"><Picture /></el-icon>
            </div>
            <div class="item-info">
              <div class="item-header">
                <h3>{{ item.item_name }}</h3>
                <span :class="['status-tag', item.status]">{{ item.status === 'lost' ? '丢失' : '已找回' }}</span>
              </div>
              <p class="item-type">{{ item.item_type }}</p>
              <p class="item-desc">{{ item.description }}</p>
              <div class="item-details">
                <div><el-icon><MapLocation /></el-icon> {{ item.location }}</div>
                <div><el-icon><Clock /></el-icon> {{ formatTime(item.lost_time) }}</div>
              </div>
              <div class="contact-info">
                <div><el-icon><User /></el-icon> {{ item.contact_person }}</div>
                <div><el-icon><Phone /></el-icon> {{ item.contact_phone || item.contact_qq }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <div v-if="total > 0" class="pagination">
      <el-pagination
        :current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { Picture, MapLocation, Clock, User, Phone } from '@element-plus/icons-vue'
import { lostItemsApi } from '../api'

const searchQuery = ref('')
const filterType = ref('')
const filterStatus = ref('')
const items = ref([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const route = useRoute()

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
  try {
    const params = {
      page: page.value,
      page_size: pageSize.value
    }
    if (filterType.value) params.item_type = filterType.value
    if (filterStatus.value) params.status = filterStatus.value
    
    const res = await lostItemsApi.getAll(params)
    items.value = res.data.items
    total.value = res.data.total
  } catch (e) {
    console.error('加载失物列表失败', e)
  }
}

const handleSearch = async () => {
  if (searchQuery.value.trim()) {
    try {
      const res = await lostItemsApi.search({
        query: searchQuery.value,
        item_type: filterType.value,
        status: filterStatus.value
      })
      items.value = res.data.results
      total.value = res.data.results.length
    } catch (e) {
      console.error('搜索失败', e)
    }
  } else {
    loadItems()
  }
}

const handlePageChange = (newPage) => {
  page.value = newPage
  loadItems()
}

const formatTime = (time) => {
  if (!time) return ''
  return new Date(time).toLocaleString('zh-CN')
}
</script>

<style scoped>
.lost-list-page {
  padding: 20px;
}

.search-bar {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.items-grid {
  margin-bottom: 20px;
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
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
}

.item-header h3 {
  font-size: 16px;
  font-weight: bold;
}

.status-tag {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 10px;
}

.status-tag.lost {
  background: #fef0f0;
  color: #F56C6C;
}

.status-tag.found {
  background: #f0f9eb;
  color: #67C23A;
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

.item-details {
  font-size: 12px;
  color: #909399;
  margin-bottom: 10px;
}

.item-details div {
  margin-bottom: 4px;
}

.contact-info {
  font-size: 12px;
  color: #606266;
  padding-top: 10px;
  border-top: 1px solid #f0f0f0;
}

.contact-info div {
  margin-bottom: 4px;
}

.pagination {
  display: flex;
  justify-content: center;
}
</style>