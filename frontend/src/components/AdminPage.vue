<template>
  <div class="admin-page">
    <h2>管理后台</h2>
    
    <div class="stats-cards">
      <el-card class="stat-card">
        <div class="stat-icon lost"><el-icon><HelpFilled /></el-icon></div>
        <div class="stat-info">
          <div class="stat-num">{{ stats.lost_count || 0 }}</div>
          <div class="stat-label">待找回</div>
        </div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-icon found"><el-icon><CircleCheck /></el-icon></div>
        <div class="stat-info">
          <div class="stat-num">{{ stats.found_count || 0 }}</div>
          <div class="stat-label">已找回</div>
        </div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-icon total"><el-icon><Box /></el-icon></div>
        <div class="stat-info">
          <div class="stat-num">{{ stats.total_items || 0 }}</div>
          <div class="stat-label">总失物</div>
        </div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-icon user"><el-icon><User /></el-icon></div>
        <div class="stat-info">
          <div class="stat-num">{{ stats.user_count || 0 }}</div>
          <div class="stat-label">用户数</div>
        </div>
      </el-card>
    </div>

    <div class="table-section">
      <h3>失物列表管理</h3>
      <el-table :data="items" border>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="item_name" label="物品名称" />
        <el-table-column prop="item_type" label="类型" width="100" />
        <el-table-column prop="location" label="地点" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.status === 'lost' ? 'danger' : 'success'">
              {{ scope.row.status === 'lost' ? '丢失' : '已找回' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="contact_person" label="联系人" width="100" />
        <el-table-column prop="created_at" label="发布时间" width="180">
          <template #default="scope">
            {{ formatTime(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="scope">
            <el-button type="text" size="small" @click="editItem(scope.row)">编辑</el-button>
            <el-button type="text" size="small" @click="deleteItem(scope.row.id)" style="color: #F56C6C;">删除</el-button>
            <el-button 
              v-if="scope.row.status === 'lost'" 
              type="text" 
              size="small" 
              @click="markFound(scope.row.id)"
              style="color: #67C23A;"
            >
              标记找回
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="dialogVisible" title="编辑失物信息">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="物品名称">
          <el-input v-model="editForm.item_name" />
        </el-form-item>
        <el-form-item label="物品类型">
          <el-select v-model="editForm.item_type">
            <el-option label="电子产品" value="电子产品" />
            <el-option label="证件卡片" value="证件卡片" />
            <el-option label="衣物鞋帽" value="衣物鞋帽" />
            <el-option label="学习用品" value="学习用品" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="详细描述">
          <el-textarea v-model="editForm.description" :rows="3" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="editForm.status">
            <el-option label="丢失" value="lost" />
            <el-option label="已找回" value="found" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { HelpFilled, CircleCheck, Box, User } from '@element-plus/icons-vue'
import { lostItemsApi, statsApi } from '../api'

const stats = ref({})
const items = ref([])
const dialogVisible = ref(false)
const editForm = reactive({
  id: null,
  item_name: '',
  item_type: '',
  description: '',
  status: 'lost'
})

onMounted(() => {
  loadStats()
  loadItems()
})

const loadStats = async () => {
  try {
    const res = await statsApi.get()
    stats.value = res.data
  } catch (e) {
    console.error('加载统计数据失败', e)
  }
}

const loadItems = async () => {
  try {
    const res = await lostItemsApi.getAll({ page: 1, page_size: 100 })
    items.value = res.data.items
  } catch (e) {
    console.error('加载失物列表失败', e)
  }
}

const editItem = (row) => {
  editForm.id = row.id
  editForm.item_name = row.item_name
  editForm.item_type = row.item_type
  editForm.description = row.description
  editForm.status = row.status
  dialogVisible.value = true
}

const saveEdit = async () => {
  try {
    const res = await lostItemsApi.update(editForm.id, {
      item_name: editForm.item_name,
      item_type: editForm.item_type,
      description: editForm.description,
      status: editForm.status
    })
    if (res.status === 200) {
      dialogVisible.value = false
      loadItems()
      loadStats()
      alert('保存成功')
    }
  } catch (e) {
    console.error('保存失败', e)
    alert('保存失败')
  }
}

const deleteItem = async (id) => {
  if (!confirm('确定要删除这条记录吗？')) return
  try {
    const res = await lostItemsApi.delete(id)
    if (res.status === 200) {
      loadItems()
      loadStats()
      alert('删除成功')
    }
  } catch (e) {
    console.error('删除失败', e)
    alert('删除失败')
  }
}

const markFound = async (id) => {
  try {
    const res = await lostItemsApi.update(id, { status: 'found' })
    if (res.status === 200) {
      loadItems()
      loadStats()
      alert('标记成功')
    }
  } catch (e) {
    console.error('标记失败', e)
    alert('标记失败')
  }
}

const formatTime = (time) => {
  if (!time) return ''
  return new Date(time).toLocaleString('zh-CN')
}
</script>

<style scoped>
.admin-page {
  padding: 20px;
}

.admin-page h2 {
  margin-bottom: 30px;
  font-size: 24px;
}

.stats-cards {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 20px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.stat-icon.lost {
  background: #fef0f0;
  color: #F56C6C;
}

.stat-icon.found {
  background: #f0f9eb;
  color: #67C23A;
}

.stat-icon.total {
  background: #ecf5ff;
  color: #409EFF;
}

.stat-icon.user {
  background: #fdf6ec;
  color: #E6A23C;
}

.stat-info .stat-num {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.stat-info .stat-label {
  font-size: 14px;
  color: #909399;
}

.table-section h3 {
  margin-bottom: 15px;
  font-size: 18px;
}
</style>