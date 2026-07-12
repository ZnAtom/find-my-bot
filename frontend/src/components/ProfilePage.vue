<template>
  <div class="profile-page" v-loading="loading">
    <div class="page-shell">
      <header class="profile-header">
        <div>
          <p class="page-kicker">Account</p>
          <h1 class="page-title">个人中心</h1>
          <p class="page-subtitle">管理自己的发布记录和默认联系方式。</p>
        </div>
        <el-button type="primary" round @click="goCreate">
          <el-icon><Plus /></el-icon>
          发布记录
        </el-button>
      </header>

      <div class="profile-layout">
        <aside class="account-panel surface-section">
          <div class="avatar">{{ userInitial }}</div>
          <h2>{{ user?.name || '未命名用户' }}</h2>
          <p>{{ user?.student_id }}</p>
          <el-tag :type="user?.role === 'admin' ? 'danger' : 'info'" effect="light">
            {{ user?.role === 'admin' ? '管理员' : '普通用户' }}
          </el-tag>

          <div class="contact-list">
            <div class="contact-line">
              <el-icon><Message /></el-icon>
              <span>{{ user?.email || '未填写邮箱' }}</span>
            </div>
            <div class="contact-line">
              <el-icon><Phone /></el-icon>
              <span>{{ user?.phone || '未填写手机' }}</span>
            </div>
            <div class="contact-line">
              <el-icon><ChatDotRound /></el-icon>
              <span>{{ user?.qq || '未填写 QQ' }}</span>
            </div>
          </div>
        </aside>

        <section class="content-panel surface-section">
          <el-tabs v-model="activeTab" class="profile-tabs">
            <el-tab-pane label="我的发布" name="items">
              <div class="items-toolbar">
                <div>
                  <strong>{{ total }}</strong>
                  <span>条记录</span>
                </div>
                <div class="toolbar-actions">
                  <el-select v-model="statusFilter" placeholder="全部状态" clearable @change="handleStatusChange">
                    <el-option label="全部状态" value="" />
                    <el-option label="进行中" value="active" />
                    <el-option label="已找回" value="recovered" />
                    <el-option label="已过期" value="expired" />
                  </el-select>
                  <el-button :icon="Refresh" circle @click="loadItems" />
                </div>
              </div>

              <el-alert
                v-if="itemsError"
                :title="itemsError"
                type="error"
                show-icon
                :closable="false"
                class="items-error"
              />

              <el-table :data="items" v-loading="itemsLoading" class="items-table">
                <el-table-column label="物品" min-width="260">
                  <template #default="scope">
                    <div class="item-cell">
                      <span class="item-thumb">
                        <img
                          v-if="firstImage(scope.row.image_url)"
                          :src="resolveImageUrl(firstImage(scope.row.image_url))"
                          alt=""
                        />
                        <el-icon v-else><Picture /></el-icon>
                      </span>
                      <span class="item-meta">
                        <strong>{{ scope.row.item_name }}</strong>
                        <small>{{ scope.row.location || '未知地点' }}</small>
                      </span>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column label="类型" width="92">
                  <template #default="scope">
                    <span class="type-chip">{{ getDirectionText(scope.row.direction) }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="状态" width="110">
                  <template #default="scope">
                    <span :class="['status-chip', getStatusClass(scope.row)]">
                      {{ getStatusText(scope.row) }}
                    </span>
                  </template>
                </el-table-column>
                <el-table-column label="发布时间" width="170">
                  <template #default="scope">{{ formatTime(scope.row.created_at) }}</template>
                </el-table-column>
                <el-table-column label="操作" width="240" fixed="right">
                  <template #default="scope">
                    <el-button type="primary" link @click="goDetail(scope.row.id)">查看</el-button>
                    <el-button type="primary" link @click="openEdit(scope.row)">编辑</el-button>
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

              <el-empty v-if="!itemsLoading && items.length === 0" description="暂无发布记录">
                <el-button type="primary" round @click="goCreate">发布第一条</el-button>
              </el-empty>

              <div v-if="total > pageSize" class="pagination">
                <el-pagination
                  background
                  layout="prev, pager, next"
                  :current-page="page"
                  :page-size="pageSize"
                  :total="total"
                  @current-change="handlePageChange"
                />
              </div>
            </el-tab-pane>

            <el-tab-pane label="联系方式" name="contact">
              <el-form ref="profileFormRef" :model="profileForm" :rules="profileRules" label-position="top" class="contact-form">
                <div class="form-grid">
                  <el-form-item label="昵称" prop="name">
                    <el-input v-model="profileForm.name" placeholder="发布时显示的名称" clearable>
                      <template #prefix><el-icon><User /></el-icon></template>
                    </el-input>
                  </el-form-item>
                  <el-form-item label="手机号" prop="phone">
                    <el-input v-model="profileForm.phone" placeholder="用于发布时自动填入" clearable>
                      <template #prefix><el-icon><Phone /></el-icon></template>
                    </el-input>
                  </el-form-item>
                  <el-form-item label="QQ" prop="qq">
                    <el-input v-model="profileForm.qq" placeholder="用于发布时自动填入" clearable>
                      <template #prefix><el-icon><ChatDotRound /></el-icon></template>
                    </el-input>
                  </el-form-item>
                  <el-form-item label="邮箱" prop="email">
                    <el-input v-model="profileForm.email" placeholder="用于通知" clearable>
                      <template #prefix><el-icon><Message /></el-icon></template>
                    </el-input>
                  </el-form-item>
                </div>
                <el-button type="primary" round :loading="savingProfile" @click="saveProfile">保存联系方式</el-button>
              </el-form>
            </el-tab-pane>

            <el-tab-pane label="账号" name="account">
              <div class="account-grid">
                <div class="account-row">
                  <span>登录来源</span>
                  <strong>Casdoor</strong>
                </div>
                <div class="account-row">
                  <span>当前角色</span>
                  <strong>{{ user?.role === 'admin' ? '管理员' : '普通用户' }}</strong>
                </div>
                <div v-if="userStore.isAdmin" class="account-row">
                  <span>当前模式</span>
                  <strong>{{ userStore.isAdminView ? '管理员' : '普通用户预览' }}</strong>
                </div>
                <div class="account-actions">
                  <el-button v-if="userStore.isAdmin" round @click="userStore.toggleView()">
                    <el-icon><Switch /></el-icon>
                    切换模式
                  </el-button>
                  <el-button round @click="logout">
                    <el-icon><SwitchButton /></el-icon>
                    退出登录
                  </el-button>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </section>
      </div>
    </div>

    <el-dialog v-model="editDialogVisible" title="编辑发布" width="600px">
      <el-form :model="editForm" label-position="top">
        <div class="form-grid">
          <el-form-item label="物品名称">
            <el-input v-model="editForm.item_name" />
          </el-form-item>
          <el-form-item label="分类">
            <el-select v-model="editForm.item_type" placeholder="选择分类">
              <el-option v-for="type in itemTypes" :key="type" :label="type" :value="type" />
            </el-select>
          </el-form-item>
        </div>
        <el-form-item label="详细描述">
          <el-input v-model="editForm.description" type="textarea" :rows="4" />
        </el-form-item>
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
        </div>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingItem" @click="saveItem">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ChatDotRound,
  Message,
  Phone,
  Picture,
  Plus,
  Refresh,
  Switch,
  SwitchButton,
  User,
} from '@element-plus/icons-vue'
import { useUserStore } from '../stores/user'
import { lostItemsApi, meApi, resolveImageUrl } from '../api'

const userStore = useUserStore()
const router = useRouter()
const activeTab = ref('items')
const loading = ref(false)
const itemsLoading = ref(false)
const savingProfile = ref(false)
const savingItem = ref(false)
const editDialogVisible = ref(false)
const profileFormRef = ref(null)
const user = computed(() => userStore.user)
const userInitial = computed(() => {
  const name = user.value?.name || user.value?.student_id || 'F'
  return String(name).slice(0, 1).toUpperCase()
})
const items = ref([])
const itemsError = ref('')
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const statusFilter = ref('')
const itemTypes = ['证件卡片', '电子产品', '衣物鞋帽', '学习用品', '钱包钥匙', '其他']

const profileForm = reactive({
  name: '',
  phone: '',
  qq: '',
  email: '',
})

const editForm = reactive({
  id: null,
  item_name: '',
  item_type: '',
  direction: 'lost',
  description: '',
  status: 'active',
})

const profileRules = {
  name: [
    { required: true, message: '请输入昵称', trigger: 'blur' },
    { max: 50, message: '昵称不能超过 50 个字符', trigger: 'blur' },
  ],
  phone: [{ pattern: /^$|^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }],
  qq: [{ pattern: /^$|^[1-9]\d{4,11}$/, message: '请输入正确的 QQ 号', trigger: 'blur' }],
  email: [{ type: 'email', message: '请输入正确的邮箱', trigger: 'blur' }],
}

onMounted(async () => {
  loading.value = true
  try {
    await userStore.fetchUser()
    if (!userStore.isAuthenticated) {
      userStore.loginWithCasdoor('/#/profile')
      return
    }
    syncProfileForm()
    await loadItems()
  } finally {
    loading.value = false
  }
})

const syncProfileForm = () => {
  profileForm.name = user.value?.name || ''
  profileForm.phone = user.value?.phone || ''
  profileForm.qq = user.value?.qq || ''
  profileForm.email = user.value?.email || ''
}

const loadItems = async () => {
  itemsLoading.value = true
  itemsError.value = ''
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (statusFilter.value) params.status = statusFilter.value
    const res = await meApi.items(params)
    items.value = res.data.items || []
    total.value = res.data.total || 0
  } catch (e) {
    console.error('加载我的发布失败', e)
    if (e.response?.status === 401) {
      userStore.loginWithCasdoor('/#/profile')
      return
    }
    items.value = []
    total.value = 0
    itemsError.value = profileApiErrorText(e, '加载我的发布失败')
  } finally {
    itemsLoading.value = false
  }
}

const saveProfile = async () => {
  try {
    await profileFormRef.value?.validate()
  } catch {
    return
  }
  savingProfile.value = true
  try {
    await meApi.update({
      name: profileForm.name,
      phone: profileForm.phone,
      qq: profileForm.qq,
      email: profileForm.email,
    })
    await userStore.fetchUser()
    syncProfileForm()
    ElMessage.success('联系方式已保存')
  } catch (e) {
    console.error('保存联系方式失败', e)
    if (e.response?.status === 401) {
      userStore.loginWithCasdoor('/#/profile')
      return
    }
    ElMessage.error(profileApiErrorText(e, '保存联系方式失败'))
  } finally {
    savingProfile.value = false
  }
}

const handleStatusChange = () => {
  page.value = 1
  loadItems()
}

const openEdit = (row) => {
  editForm.id = row.id
  editForm.item_name = row.item_name
  editForm.item_type = row.item_type || ''
  editForm.direction = row.direction || row.post_type || 'lost'
  editForm.description = row.description || ''
  editForm.status = row.status || 'active'
  editDialogVisible.value = true
}

const saveItem = async () => {
  savingItem.value = true
  try {
    await lostItemsApi.update(editForm.id, {
      item_name: editForm.item_name,
      item_type: editForm.item_type,
      direction: editForm.direction,
      description: editForm.description,
      status: editForm.status,
    })
    editDialogVisible.value = false
    ElMessage.success('发布信息已保存')
    await loadItems()
  } catch (e) {
    console.error('保存发布失败', e)
    ElMessage.error('保存发布失败')
  } finally {
    savingItem.value = false
  }
}

const markResolved = async (id) => {
  try {
    await lostItemsApi.update(id, { status: 'recovered' })
    ElMessage.success('已标记为已找回')
    await loadItems()
  } catch (e) {
    console.error('标记失败', e)
    ElMessage.error('标记失败')
  }
}

const deleteItem = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这条发布吗？', '删除确认', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    await lostItemsApi.delete(id)
    ElMessage.success('已删除')
    await loadItems()
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') {
      console.error('删除失败', e)
      ElMessage.error('删除失败')
    }
  }
}

const handlePageChange = (nextPage) => {
  page.value = nextPage
  loadItems()
}

const firstImage = (url) => {
  if (!url) return ''
  return url.split(',').map(v => v.trim()).filter(Boolean)[0] || ''
}

const apiErrorText = (error, fallback) => {
  const detail = error?.response?.data?.detail
  if (Array.isArray(detail)) return detail.map(item => item.msg).filter(Boolean).join('；') || fallback
  return detail || fallback
}

const profileApiErrorText = (error, fallback) => {
  if (error?.response?.status === 404) {
    return '个人中心后端接口未部署，请更新并重启后端服务'
  }
  return apiErrorText(error, fallback)
}

const formatTime = (time) => {
  if (!time) return ''
  return new Date(time).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const goDetail = (id) => {
  router.push({ name: 'detail', params: { id } })
}

const goCreate = () => {
  router.push({ name: 'create' })
}

const logout = async () => {
  await userStore.logout()
  router.push({ name: 'home' })
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
.profile-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 22px;
}

.profile-layout {
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr);
  gap: 18px;
  align-items: start;
}

.account-panel {
  padding: 22px;
}

.avatar {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  color: #fff;
  background: linear-gradient(135deg, var(--foundit-blue), var(--foundit-teal));
  font-size: 24px;
  font-weight: 800;
}

.account-panel h2 {
  margin: 16px 0 6px;
  font-size: 22px;
  font-weight: 800;
}

.account-panel p {
  margin: 0 0 12px;
  color: var(--text-secondary);
  font-size: 13px;
  word-break: break-all;
}

.contact-list {
  display: grid;
  gap: 10px;
  margin-top: 22px;
}

.contact-line {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  color: var(--text-secondary);
  font-size: 13px;
}

.contact-line span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.content-panel {
  padding: 0 20px 20px;
}

.items-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 14px;
  margin-bottom: 16px;
}

.items-toolbar strong {
  color: var(--text-primary);
  font-size: 22px;
}

.items-toolbar span {
  color: var(--text-secondary);
  margin-left: 4px;
}

.toolbar-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.items-error {
  margin-bottom: 14px;
}

.item-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.item-thumb {
  width: 46px;
  height: 46px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  border-radius: var(--border-radius-md);
  overflow: hidden;
  color: #94a3b8;
  background: var(--surface-muted);
}

.item-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.item-meta {
  min-width: 0;
}

.item-meta strong,
.item-meta small {
  display: block;
}

.item-meta strong {
  color: var(--text-primary);
  font-weight: 800;
}

.item-meta small {
  margin-top: 3px;
  color: var(--text-secondary);
  font-size: 12px;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 18px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.contact-form {
  max-width: 760px;
}

.account-grid {
  display: grid;
  gap: 12px;
  max-width: 560px;
}

.account-row {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  padding: 14px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  background: var(--surface-muted);
}

.account-row span {
  color: var(--text-secondary);
}

.account-actions {
  display: flex;
  gap: 10px;
  margin-top: 6px;
}

@media (max-width: 920px) {
  .profile-layout {
    grid-template-columns: 1fr;
  }

  .profile-header,
  .items-toolbar {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 640px) {
  .form-grid {
    grid-template-columns: 1fr;
  }

  .content-panel {
    padding: 0 14px 16px;
  }
}
</style>
