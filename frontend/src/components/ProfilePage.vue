<template>
  <div class="profile-page" v-loading="loading">
    <div class="page-heading">
      <div>
        <h1>个人中心</h1>
        <p>{{ user?.name || user?.student_id || '已登录用户' }}</p>
      </div>
      <el-button type="primary" round @click="goCreate">
        <el-icon><Plus /></el-icon>
        发布寻物/招领
      </el-button>
    </div>

    <div class="profile-layout">
      <aside class="profile-panel">
        <div class="avatar">
          <el-icon><User /></el-icon>
        </div>
        <h2>{{ user?.name || '未命名用户' }}</h2>
        <div class="student-id">{{ user?.student_id }}</div>
        <el-tag :type="user?.role === 'admin' ? 'danger' : 'info'" effect="light">
          {{ user?.role === 'admin' ? '管理员' : '普通用户' }}
        </el-tag>

        <div class="profile-facts">
          <div class="fact-row">
            <el-icon><Message /></el-icon>
            <span>{{ user?.email || '未填写邮箱' }}</span>
          </div>
          <div class="fact-row">
            <el-icon><Phone /></el-icon>
            <span>{{ user?.phone || '未填写手机' }}</span>
          </div>
          <div class="fact-row">
            <el-icon><ChatDotRound /></el-icon>
            <span>{{ user?.qq || '未填写 QQ' }}</span>
          </div>
        </div>

        <div class="completion">
          <div class="completion-row">
            <span>资料完整度</span>
            <strong>{{ completion }}%</strong>
          </div>
          <el-progress :percentage="completion" :show-text="false" :stroke-width="8" />
        </div>
      </aside>

      <section class="profile-content">
        <el-tabs v-model="activeTab" class="profile-tabs">
          <el-tab-pane label="我的发布" name="items">
            <div class="items-toolbar">
              <div class="toolbar-title">
                <el-icon><Document /></el-icon>
                <span>共 {{ total }} 条记录</span>
              </div>
              <div class="toolbar-actions">
                <el-select v-model="statusFilter" placeholder="全部状态" clearable @change="handleStatusChange">
                  <el-option label="全部状态" value="" />
                  <el-option label="匹配中" value="active" />
                  <el-option label="已找回" value="recovered" />
                  <el-option label="过期" value="expired" />
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
                    <img
                      v-if="firstImage(scope.row.image_url)"
                      :src="resolveImageUrl(firstImage(scope.row.image_url))"
                      alt=""
                      class="item-thumb"
                    />
                    <div v-else class="item-thumb placeholder">
                      <el-icon><Picture /></el-icon>
                    </div>
                    <div class="item-meta">
                      <strong>{{ scope.row.item_name }}</strong>
                      <span>{{ scope.row.location || '未知地点' }}</span>
                    </div>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="item_type" label="分类" width="120">
                <template #default="scope">{{ scope.row.item_type || '未分类' }}</template>
              </el-table-column>
              <el-table-column label="状态" width="120">
                <template #default="scope">
                  <el-tag :type="statusTagType(scope.row.status)" size="small">
                    {{ statusText(scope.row.status, scope.row.direction) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="发布时间" width="180">
                <template #default="scope">{{ formatTime(scope.row.created_at) }}</template>
              </el-table-column>
              <el-table-column label="操作" width="220" fixed="right">
                <template #default="scope">
                  <el-button type="primary" link @click="goDetail(scope.row.id)">查看</el-button>
                  <el-button type="primary" link @click="openEdit(scope.row)">编辑</el-button>
                  <el-button
                    v-if="scope.row.status === 'active'"
                    type="success"
                    link
                    @click="markFound(scope.row.id)"
                  >
                    标记解决
                  </el-button>
                  <el-button type="danger" link @click="deleteItem(scope.row.id)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>

            <el-empty v-if="!itemsLoading && items.length === 0" description="暂无发布记录">
              <el-button type="primary" round @click="goCreate">发布第一条信息</el-button>
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
            <el-form ref="profileFormRef" :model="profileForm" :rules="profileRules" label-width="88px" class="contact-form">
              <el-form-item label="昵称" prop="name">
                <el-input v-model="profileForm.name" placeholder="发布时显示的名称，保护真实姓名" clearable>
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
                <el-input v-model="profileForm.email" placeholder="用于平台通知" clearable>
                  <template #prefix><el-icon><Message /></el-icon></template>
                </el-input>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" round :loading="savingProfile" @click="saveProfile">保存</el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>

          <el-tab-pane label="账号与权限" name="account">
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
                <span>当前视角</span>
                <strong>{{ userStore.isAdminView ? '管理员视角' : '普通用户预览' }}</strong>
              </div>
              <div class="account-actions">
                <el-button v-if="userStore.isAdmin" round @click="userStore.toggleView()">
                  <el-icon><Switch /></el-icon>
                  切换视角
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

    <el-dialog v-model="editDialogVisible" title="编辑发布" width="560px">
      <el-form :model="editForm" label-width="88px">
        <el-form-item label="物品名称">
          <el-input v-model="editForm.item_name" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="editForm.item_type" placeholder="选择分类">
            <el-option label="电子产品" value="电子产品" />
            <el-option label="证件卡片" value="证件卡片" />
            <el-option label="衣物鞋帽" value="衣物鞋帽" />
            <el-option label="学习用品" value="学习用品" />
            <el-option label="钱包钥匙" value="钱包钥匙" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="详细描述">
          <el-input v-model="editForm.description" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item label="信息类型">
          <el-radio-group v-model="editForm.direction">
            <el-radio-button value="lost">寻物</el-radio-button>
            <el-radio-button value="found">招领</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="editForm.status">
            <el-radio-button value="active">匹配中</el-radio-button>
            <el-radio-button value="recovered">已找回</el-radio-button>
            <el-radio-button value="expired">过期</el-radio-button>
          </el-radio-group>
        </el-form-item>
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
  Document,
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
const items = ref([])
const itemsError = ref('')
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const statusFilter = ref('')

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

const completion = computed(() => {
  const fields = [user.value?.name, user.value?.email, user.value?.phone, user.value?.qq]
  return Math.round((fields.filter(Boolean).length / fields.length) * 100)
})

const statusText = (status, direction) => {
  if (status === 'recovered') return '已找回'
  if (status === 'expired') return '过期'
  return direction === 'found' ? '找主中' : '找物中'
}

const statusTagType = (status) => {
  if (status === 'recovered') return 'success'
  if (status === 'expired') return 'info'
  return 'warning'
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
  editForm.direction = row.direction || 'lost'
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

const markFound = async (id) => {
  try {
    await lostItemsApi.update(id, { status: 'recovered' })
    ElMessage.success('已标记为解决')
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
</script>

<style scoped>
.profile-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 28px 20px 48px;
}

.page-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.page-heading h1 {
  margin: 0;
  font-size: 28px;
  color: var(--text-primary);
}

.page-heading p {
  margin: 6px 0 0;
  color: var(--text-secondary);
}

.profile-layout {
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr);
  gap: 20px;
  align-items: start;
}

.profile-panel,
.profile-content {
  border-radius: 8px;
  background: var(--surface-color);
  border: 1px solid var(--border-color);
}

.profile-panel {
  padding: 24px;
}

.avatar {
  width: 68px;
  height: 68px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(124, 58, 237, 0.1), rgba(59, 130, 246, 0.1));
  color: var(--brand-primary);
  font-size: 30px;
  margin-bottom: 16px;
}

.profile-panel h2 {
  margin: 0 0 6px;
  font-size: 22px;
  color: var(--text-primary);
}

.student-id {
  color: var(--text-secondary);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 13px;
  margin-bottom: 12px;
  word-break: break-all;
}

.profile-facts {
  margin-top: 24px;
  display: grid;
  gap: 12px;
}

.fact-row {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--text-secondary);
  min-width: 0;
}

.fact-row span {
  overflow: hidden;
  text-overflow: ellipsis;
}

.fact-row .el-icon {
  color: var(--brand-primary);
  flex-shrink: 0;
}

.completion {
  margin-top: 24px;
}

.completion-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  color: var(--text-secondary);
}

.completion-row strong {
  color: var(--text-primary);
}

.profile-content {
  padding: 4px 22px 22px;
  min-width: 0;
}

.items-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin: 8px 0 16px;
}

.toolbar-title,
.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.toolbar-title {
  color: var(--text-secondary);
}

.toolbar-actions .el-select {
  width: 140px;
}

.items-table {
  width: 100%;
}

.items-error {
  margin-bottom: 14px;
}

.item-cell {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.item-thumb {
  width: 56px;
  height: 56px;
  border-radius: 8px;
  object-fit: cover;
  background: #f1f5f9;
  flex-shrink: 0;
}

.item-thumb.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
}

.item-meta {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.item-meta strong,
.item-meta span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-meta span {
  color: var(--text-secondary);
  font-size: 13px;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 18px;
}

.contact-form {
  max-width: 520px;
  padding-top: 12px;
}

.account-grid {
  max-width: 560px;
  padding-top: 8px;
  display: grid;
  gap: 14px;
}

.account-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 14px 0;
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);
}

.account-row span {
  color: var(--text-secondary);
}

.account-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  padding-top: 8px;
}

@media (max-width: 900px) {
  .profile-layout {
    grid-template-columns: 1fr;
  }

  .profile-panel {
    display: grid;
    grid-template-columns: auto 1fr;
    column-gap: 16px;
  }

  .profile-facts,
  .completion {
    grid-column: 1 / -1;
  }
}

@media (max-width: 640px) {
  .profile-page {
    padding: 20px 12px 36px;
  }

  .page-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .profile-content {
    padding: 2px 12px 16px;
  }

  .items-toolbar {
    align-items: stretch;
    flex-direction: column;
  }

  .toolbar-actions {
    justify-content: space-between;
  }
}
</style>
