<template>
  <div class="admin-page" v-loading="loading" element-loading-text="加载中">
    <div class="page-shell">
      <header class="admin-header">
        <div>
          <p class="page-kicker">Admin Console</p>
          <h1 class="page-title">管理台</h1>
          <p class="page-subtitle">维护物品记录、用户权限和向量数据状态。</p>
        </div>
        <el-button round :icon="Refresh" @click="loadAll">刷新</el-button>
      </header>

      <section class="admin-metrics">
        <div v-for="s in statCards" :key="s.label" class="metric-card">
          <div :class="['metric-label', s.cls]">
            <el-icon><component :is="s.icon" /></el-icon>
            {{ s.label }}
          </div>
          <div class="metric-value">{{ s.value }}</div>
        </div>
      </section>

      <section class="surface-section admin-panel">
        <el-tabs v-model="activeTab">
          <el-tab-pane label="物品记录" name="items">
            <el-table :data="items" v-loading="loading">
              <el-table-column prop="id" label="ID" width="70" />
              <el-table-column label="物品" min-width="220">
                <template #default="scope">
                  <div class="item-title-cell">
                    <strong>{{ scope.row.item_name }}</strong>
                    <small>{{ scope.row.location || '未知地点' }}</small>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="类型" width="92">
                <template #default="scope">
                  <span class="type-chip">{{ getDirectionText(scope.row.direction) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="item_type" label="分类" width="110" />
              <el-table-column label="存放处" min-width="140">
                <template #default="scope">{{ scope.row.storage_location || '-' }}</template>
              </el-table-column>
              <el-table-column label="联系方式" width="110">
                <template #default="scope">{{ visibilityText(scope.row.contact_visibility) }}</template>
              </el-table-column>
              <el-table-column label="状态" width="110">
                <template #default="scope">
                  <span :class="['status-chip', getStatusClass(scope.row)]">
                    {{ getStatusText(scope.row) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="contact_person" label="联系人" width="110" />
              <el-table-column label="向量" width="190">
                <template #default="scope">
                  <template v-if="scope.row.vector">
                    <span class="vector-summary">{{ vectorSummary(scope.row.vector) }}</span>
                    <el-button type="primary" link size="small" @click="showVector(scope.row)">详情</el-button>
                  </template>
                  <span v-else class="no-vector">未生成</span>
                </template>
              </el-table-column>
              <el-table-column label="发布时间" width="180">
                <template #default="scope">
                  {{ formatTime(scope.row.created_at) }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="220" fixed="right">
                <template #default="scope">
                  <el-button type="primary" link @click="goDetail(scope.row.id)">查看</el-button>
                  <el-button type="primary" link @click="editItem(scope.row)">编辑</el-button>
                  <el-button
                    v-if="scope.row.status === 'active'"
                    type="success"
                    link
                    @click="markResolved(scope.row.id)"
                  >
                    标记解决
                  </el-button>
                  <el-button type="danger" link @click="deleteItem(scope.row.id)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <el-tab-pane label="申请" name="claims">
            <el-table :data="claims" v-loading="loadingClaims">
              <el-table-column prop="id" label="ID" width="70" />
              <el-table-column prop="item_name" label="物品" min-width="160" />
              <el-table-column label="类型" width="100">
                <template #default="scope">
                  <el-tag :type="scope.row.request_type === 'claim' ? 'success' : 'primary'" size="small">
                    {{ scope.row.request_type === 'claim' ? '认领' : '联系' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="requester_name" label="申请人" width="120" />
              <el-table-column prop="requester_contact" label="联系方式" min-width="180" />
              <el-table-column prop="message" label="补充说明" min-width="220">
                <template #default="scope">{{ scope.row.message || '-' }}</template>
              </el-table-column>
              <el-table-column label="发布者" width="130">
                <template #default="scope">{{ scope.row.owner_user_name || '匿名/未绑定' }}</template>
              </el-table-column>
              <el-table-column label="状态" width="100">
                <template #default="scope">{{ claimStatusText(scope.row.status) }}</template>
              </el-table-column>
              <el-table-column label="申请时间" width="180">
                <template #default="scope">{{ formatTime(scope.row.created_at) }}</template>
              </el-table-column>
              <el-table-column label="操作" width="90" fixed="right">
                <template #default="scope">
                  <el-button type="primary" link @click="goDetail(scope.row.item_id)">查看</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <el-tab-pane label="用户" name="users">
            <el-table :data="users" v-loading="loadingUsers">
              <el-table-column prop="id" label="ID" width="70" />
              <el-table-column prop="name" label="姓名" width="140" />
              <el-table-column prop="student_id" label="学号 / Casdoor ID" min-width="220">
                <template #default="scope">
                  <span class="mono">{{ scope.row.student_id }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="email" label="邮箱" min-width="200" />
              <el-table-column label="角色" width="110">
                <template #default="scope">
                  <el-tag :type="scope.row.role === 'admin' ? 'danger' : 'info'" size="small">
                    {{ scope.row.role === 'admin' ? '管理员' : '普通用户' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="注册时间" width="180">
                <template #default="scope">{{ formatTime(scope.row.created_at) }}</template>
              </el-table-column>
              <el-table-column label="操作" width="160" fixed="right">
                <template #default="scope">
                  <el-button
                    v-if="scope.row.role === 'user'"
                    type="primary"
                    link
                    @click="promoteUser(scope.row.id)"
                  >
                    设为管理员
                  </el-button>
                  <el-button
                    v-else-if="scope.row.id !== userStore.user?.id"
                    type="warning"
                    link
                    @click="demoteUser(scope.row.id)"
                  >
                    设为普通用户
                  </el-button>
                  <span v-else class="self-role-note">当前账号</span>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </section>
    </div>

    <el-dialog v-model="vectorDialogVisible" title="向量详情" width="760px">
      <template v-if="selectedItem">
        <p><strong>物品：</strong>{{ selectedItem.item_name }}</p>
        <p><strong>向量维度：</strong>{{ vectorParsed(selectedItem.vector).length }}</p>
        <div class="vector-full">{{ vectorParsed(selectedItem.vector).join(', ') }}</div>
      </template>
    </el-dialog>

    <el-dialog v-model="dialogVisible" title="编辑物品记录" width="620px">
      <el-form :model="editForm" label-position="top">
        <div class="form-grid">
          <el-form-item label="物品名称">
            <el-input v-model="editForm.item_name" />
          </el-form-item>
          <el-form-item label="物品类型">
            <el-select v-model="editForm.item_type">
              <el-option v-for="type in itemTypes" :key="type" :label="type" :value="type" />
            </el-select>
          </el-form-item>
        </div>
        <el-form-item label="详细描述">
          <el-input type="textarea" v-model="editForm.description" :rows="4" />
        </el-form-item>
        <div class="form-grid">
          <el-form-item label="地点">
            <el-input v-model="editForm.location" />
          </el-form-item>
          <el-form-item label="当前存放处">
            <el-input v-model="editForm.storage_location" />
          </el-form-item>
        </div>
        <div class="form-grid">
          <el-form-item label="信息类型">
            <el-radio-group v-model="editForm.direction">
              <el-radio-button value="lost">寻物</el-radio-button>
              <el-radio-button value="found">招领</el-radio-button>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="状态">
            <el-radio-group v-model="editForm.status">
              <el-radio-button value="active">进行中</el-radio-button>
              <el-radio-button value="recovered">已找回</el-radio-button>
              <el-radio-button value="expired">已过期</el-radio-button>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="联系方式可见性">
            <el-select v-model="editForm.contact_visibility">
              <el-option label="隐藏" value="private" />
              <el-option label="登录可见" value="logged_in" />
              <el-option label="认领后可见" value="claimed" />
              <el-option label="公开" value="public" />
            </el-select>
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Box, CircleCheck, HelpFilled, Refresh, User } from '@element-plus/icons-vue'
import { lostItemsApi, statsApi, usersApi, claimsApi } from '../api'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const router = useRouter()
const activeTab = ref('items')
const stats = ref({})
const items = ref([])
const users = ref([])
const claims = ref([])
const loading = ref(true)
const loadingUsers = ref(true)
const loadingClaims = ref(true)
const dialogVisible = ref(false)
const vectorDialogVisible = ref(false)
const selectedItem = ref(null)
const itemTypes = ['电子产品', '证件卡片', '衣物鞋帽', '学习用品', '钱包钥匙', '其他']

const editForm = reactive({
  id: null,
  item_name: '',
  item_type: '',
  direction: 'lost',
  description: '',
  location: '',
  storage_location: '',
  status: 'active',
  contact_visibility: 'private',
})

const statCards = computed(() => [
  { label: '正在寻找', value: stats.value.lost_count || 0, icon: HelpFilled, cls: 'danger' },
  { label: '等待认领', value: stats.value.found_count || 0, icon: CircleCheck, cls: 'success' },
  { label: '总记录', value: stats.value.total_items || 0, icon: Box, cls: '' },
  { label: '用户', value: stats.value.user_count || 0, icon: User, cls: '' },
])

const visibilityText = (visibility) => {
  if (visibility === 'public') return '公开'
  if (visibility === 'logged_in') return '登录可见'
  if (visibility === 'claimed') return '认领后'
  return '隐藏'
}

const claimStatusText = (status) => {
  if (status === 'completed') return '已完成'
  if (status === 'rejected') return '已拒绝'
  return '已提交'
}

onMounted(() => {
  if (!userStore.isAdminView) {
    router.replace({ name: 'home' })
    return
  }
  loadAll()
})

watch(() => userStore.isAdminView, (isAdminView) => {
  if (!isAdminView) {
    router.replace({ name: 'home' })
  }
})

const loadAll = async () => {
  loading.value = true
  loadingUsers.value = true
  loadingClaims.value = true
  try {
    const [statsRes, itemsRes, usersRes, claimsRes] = await Promise.all([
      statsApi.get(),
      lostItemsApi.getAll({ page: 1, page_size: 100 }),
      usersApi.getAll(),
      claimsApi.adminList({ limit: 100 }),
    ])
    stats.value = statsRes.data
    items.value = itemsRes.data.items || []
    users.value = usersRes.data || []
    claims.value = claimsRes.data || []
  } catch (e) {
    console.error('加载失败', e)
  } finally {
    loading.value = false
    loadingUsers.value = false
    loadingClaims.value = false
  }
}

const promoteUser = async (userId) => {
  try {
    await usersApi.update(userId, { role: 'admin' })
    ElMessage.success('已设为管理员')
    loadAll()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const demoteUser = async (userId) => {
  try {
    await ElMessageBox.confirm('确定要设为普通用户吗？', '确认操作', {
      type: 'warning',
      confirmButtonText: '确定',
      cancelButtonText: '取消',
    })
    await usersApi.update(userId, { role: 'user' })
    ElMessage.success('已设为普通用户')
    loadAll()
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') {
      ElMessage.error('操作失败')
    }
  }
}

const goDetail = (id) => {
  router.push({ name: 'detail', params: { id } })
}

const editItem = (row) => {
  editForm.id = row.id
  editForm.item_name = row.item_name
  editForm.item_type = row.item_type
  editForm.direction = row.direction || row.post_type || 'lost'
  editForm.description = row.description
  editForm.location = row.location || ''
  editForm.storage_location = row.storage_location || ''
  editForm.status = row.status
  editForm.contact_visibility = row.contact_visibility || 'private'
  dialogVisible.value = true
}

const saveEdit = async () => {
  try {
    await lostItemsApi.update(editForm.id, {
      item_name: editForm.item_name,
      item_type: editForm.item_type,
      direction: editForm.direction,
      description: editForm.description,
      location: editForm.location,
      storage_location: editForm.storage_location,
      status: editForm.status,
      contact_visibility: editForm.contact_visibility,
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
    await ElMessageBox.confirm('确定要删除这条记录吗？', '删除确认', {
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

const markResolved = async (id) => {
  try {
    await lostItemsApi.update(id, { status: 'recovered' })
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
  const arr = vectorParsed(vec)
  if (arr.length === 0) return '无'
  return `[${arr.slice(0, 3).map(v => Number(v).toFixed(4)).join(', ')}, ...] ${arr.length}维`
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

const getDirectionText = (direction) => direction === 'found' ? '招领' : '寻物'

const getStatusClass = (row) => {
  if (row.status === 'recovered') return 'recovered'
  if (row.status === 'expired') return 'expired'
  return row.direction === 'lost' ? 'lost' : 'found'
}

const getStatusText = (row) => {
  if (row.status === 'recovered') return '已找回'
  if (row.status === 'expired') return '已过期'
  return row.direction === 'lost' ? '待找回' : '招领中'
}
</script>

<style scoped>
.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 22px;
}

.admin-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 18px;
}

.metric-label.success {
  color: var(--success-color);
}

.metric-label.danger {
  color: var(--danger-color);
}

.admin-panel {
  padding: 0 18px 18px;
}

.item-title-cell strong,
.item-title-cell small {
  display: block;
}

.item-title-cell strong {
  color: var(--text-primary);
  font-weight: 800;
}

.item-title-cell small {
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 12px;
}

.vector-summary,
.mono,
.vector-full {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

.vector-summary {
  color: var(--text-secondary);
  font-size: 11px;
}

.no-vector {
  color: var(--danger-color);
  font-size: 12px;
  font-weight: 700;
}

.self-role-note {
  color: var(--text-secondary);
  font-size: 12px;
}

.vector-full {
  max-height: 420px;
  overflow-y: auto;
  padding: 12px;
  border-radius: var(--border-radius-md);
  background: var(--surface-muted);
  color: var(--text-secondary);
  font-size: 11px;
  line-height: 1.8;
  word-break: break-all;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

@media (max-width: 900px) {
  .admin-header {
    flex-direction: column;
  }

  .admin-metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .admin-metrics,
  .form-grid {
    grid-template-columns: 1fr;
  }

  .admin-panel {
    padding: 0 12px 14px;
  }
}
</style>
