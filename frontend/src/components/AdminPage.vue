<template>
  <div class="admin-page" v-loading="loading" element-loading-text="加载中...">
    <h2>管理后台</h2>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-card class="stat-card" v-for="s in statCards" :key="s.label">
        <template v-if="loading">
          <el-skeleton animated>
            <template #template>
              <div style="display:flex;align-items:center;gap:20px">
                <el-skeleton-item variant="circle" style="width:60px;height:60px" />
                <div>
                  <el-skeleton-item variant="text" style="width:60px;height:28px" />
                  <el-skeleton-item variant="text" style="width:40px;height:14px" />
                </div>
              </div>
            </template>
          </el-skeleton>
        </template>
        <template v-else>
          <div :class="['stat-icon', s.cls]"><el-icon><component :is="s.icon" /></el-icon></div>
          <div class="stat-info">
            <div class="stat-num">{{ s.value }}</div>
            <div class="stat-label">{{ s.label }}</div>
          </div>
        </template>
      </el-card>
    </div>

    <!-- 表格 -->
    <div class="table-section">
      <h3>失物列表管理</h3>
      <el-table :data="items" border v-loading="loading">
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
        <el-table-column label="向量" width="180">
          <template #default="scope">
            <template v-if="scope.row.vector">
              <span class="vector-summary">{{ vectorSummary(scope.row.vector) }}</span>
              <el-button type="primary" link size="small" @click="showVector(scope.row)">详情</el-button>
            </template>
            <span v-else class="no-vector">未向量化</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="发布时间" width="180">
          <template #default="scope">
            {{ formatTime(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button type="text" size="small" @click="goDetail(scope.row.id)">查看</el-button>
            <el-button type="text" size="small" @click="editItem(scope.row)">编辑</el-button>
            <el-button type="text" size="small" @click="deleteItem(scope.row.id)" style="color: #F56C6C">删除</el-button>
            <el-button
              v-if="scope.row.status === 'lost'"
              type="text" size="small" @click="markFound(scope.row.id)"
              style="color: #67C23A"
            >
              标记找回
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 向量详情弹窗 -->
    <el-dialog v-model="vectorDialogVisible" title="向量详情" width="700px">
      <template v-if="selectedItem">
        <p><strong>物品：</strong>{{ selectedItem.item_name }}</p>
        <p><strong>向量维度：</strong>{{ vectorParsed(selectedItem.vector).length }}</p>
        <div class="vector-full">{{ vectorParsed(selectedItem.vector).join(', ') }}</div>
      </template>
    </el-dialog>

    <!-- 编辑弹窗 -->
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
          <el-input type="textarea" v-model="editForm.description" :rows="3" />
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
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { HelpFilled, CircleCheck, Box, User } from '@element-plus/icons-vue'
import { lostItemsApi, statsApi } from '../api'

const router = useRouter()
const stats = ref({})
const items = ref([])
const loading = ref(true)
const dialogVisible = ref(false)
const vectorDialogVisible = ref(false)
const selectedItem = ref(null)
const editForm = reactive({
  id: null,
  item_name: '',
  item_type: '',
  description: '',
  status: 'lost',
})

const statCards = computed(() => [
  { label: '待找回', value: stats.value.lost_count || 0, icon: HelpFilled, cls: 'lost' },
  { label: '已找回', value: stats.value.found_count || 0, icon: CircleCheck, cls: 'found' },
  { label: '总失物', value: stats.value.total_items || 0, icon: Box, cls: 'total' },
  { label: '用户数', value: stats.value.user_count || 0, icon: User, cls: 'user' },
])

onMounted(() => {
  loadAll()
})

const loadAll = async () => {
  loading.value = true
  try {
    const [statsRes, itemsRes] = await Promise.all([
      statsApi.get(),
      lostItemsApi.getAll({ page: 1, page_size: 100 }),
    ])
    stats.value = statsRes.data
    items.value = itemsRes.data.items
  } catch (e) {
    console.error('加载失败', e)
  } finally {
    loading.value = false
  }
}

const goDetail = (id) => {
  router.push({ name: 'detail', params: { id } })
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
    await lostItemsApi.update(editForm.id, {
      item_name: editForm.item_name,
      item_type: editForm.item_type,
      description: editForm.description,
      status: editForm.status,
    })
    dialogVisible.value = false
    ElMessage.success('保存成功')
    loadAll()
  } catch (e) {
    console.error('保存失败', e)
    ElMessage.error('保存失败')
  }
}

const deleteItem = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这条记录吗？', '警告', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    await lostItemsApi.delete(id)
    ElMessage.success('删除成功')
    loadAll()
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') {
      console.error('删除失败', e)
      ElMessage.error('删除失败')
    }
  }
}

const markFound = async (id) => {
  try {
    await lostItemsApi.update(id, { status: 'found' })
    ElMessage.success('标记成功')
    loadAll()
  } catch (e) {
    console.error('标记失败', e)
    ElMessage.error('标记失败')
  }
}

const formatTime = (time) => {
  if (!time) return ''
  return new Date(time).toLocaleString('zh-CN')
}

const vectorSummary = (vec) => {
  const arr = Array.isArray(vec) ? vec : JSON.parse(vec.replace(/\(/g, '[').replace(/\)/g, ']'))
  if (arr.length === 0) return '无'
  return `[${arr.slice(0, 5).map(v => Number(v).toFixed(4)).join(', ')}, ...] ${arr.length}维`
}

const vectorParsed = (vec) => {
  if (!vec) return []
  const arr = Array.isArray(vec) ? vec : JSON.parse(vec.replace(/\(/g, '[').replace(/\)/g, ']'))
  return arr.map(v => Number(v))
}

const showVector = (row) => {
  selectedItem.value = row
  vectorDialogVisible.value = true
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
}

.stat-card :deep(.el-card__body) {
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
  flex-shrink: 0;
}

.stat-icon.lost { background: #fef0f0; color: #F56C6C; }
.stat-icon.found { background: #f0f9eb; color: #67C23A; }
.stat-icon.total { background: #ecf5ff; color: #409EFF; }
.stat-icon.user { background: #fdf6ec; color: #E6A23C; }

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

.vector-summary {
  font-family: monospace;
  font-size: 11px;
  color: #606266;
  margin-right: 8px;
}

.no-vector {
  color: #F56C6C;
  font-size: 12px;
}

.vector-full {
  font-family: monospace;
  font-size: 11px;
  max-height: 400px;
  overflow-y: auto;
  word-break: break-all;
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  line-height: 1.8;
}

/* ===== 响应式 ===== */
@media (max-width: 768px) {
  .admin-page {
    padding: 12px;
  }

  .admin-page h2 {
    font-size: 20px;
    margin-bottom: 16px;
  }

  .stats-cards {
    flex-wrap: wrap;
    gap: 10px;
    margin-bottom: 16px;
  }

  .stat-card {
    flex: 1 1 calc(50% - 10px);
    min-width: 140px;
  }

  .stat-card :deep(.el-card__body) {
    gap: 10px;
    padding: 12px;
  }

  .stat-icon {
    width: 44px;
    height: 44px;
    font-size: 18px;
  }

  .stat-info .stat-num {
    font-size: 22px;
  }

  .stat-info .stat-label {
    font-size: 12px;
  }

  .table-section h3 {
    font-size: 16px;
  }

  /* 表格横向滚动 */
  .table-section :deep(.el-table) {
    font-size: 12px;
  }

  .table-section :deep(.el-table__body-wrapper) {
    overflow-x: auto;
  }
}
</style>
