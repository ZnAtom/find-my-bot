<template>
  <div class="detail-page">
    <div class="page-shell">
      <template v-if="loading">
        <div class="surface-section skeleton-wrap">
          <el-skeleton animated>
            <template #template>
              <div class="detail-layout">
                <el-skeleton-item variant="image" style="height: 460px" />
                <div>
                  <el-skeleton-item variant="text" style="width: 66%; height: 42px" />
                  <el-skeleton-item variant="text" style="width: 42%; margin-top: 18px" />
                  <el-skeleton-item variant="text" style="width: 100%; margin-top: 38px" />
                  <el-skeleton-item variant="text" style="width: 80%; margin-top: 12px" />
                </div>
              </div>
            </template>
          </el-skeleton>
        </div>
      </template>

      <template v-else-if="item">
        <div class="top-bar">
          <el-button round @click="goBack">
            <el-icon><ArrowLeft /></el-icon>
            返回
          </el-button>
        </div>

        <section class="detail-layout">
          <div class="gallery-panel surface-section">
            <div class="image-frame main-image">
              <el-image
                v-if="currentImage"
                class="main-image-content"
                :src="resolveImageUrl(currentImage)"
                fit="contain"
                :preview-src-list="imageList.map(u => resolveImageUrl(u))"
                :initial-index="currentImageIndex"
                preview-teleported
              >
                <template #error>
                  <div class="image-placeholder">
                    <el-icon size="54"><Picture /></el-icon>
                  </div>
                </template>
              </el-image>
              <div v-else class="image-placeholder">
                <el-icon size="54"><PictureFilled /></el-icon>
              </div>
            </div>

            <div v-if="imageList.length > 1" class="thumb-row">
              <button
                v-for="(img, idx) in imageList"
                :key="img"
                :class="['thumb-button', { active: currentImageIndex === idx }]"
                type="button"
                @click="currentImageIndex = idx"
              >
                <img :src="resolveImageUrl(img)" alt="" />
              </button>
            </div>
          </div>

          <div class="info-stack">
            <header class="item-header">
              <div class="badge-row">
                <span :class="['status-chip', getStatusClass(item)]">{{ getStatusText(item) }}</span>
                <span class="type-chip">{{ getDirectionText(item.direction) }}</span>
              </div>
              <h1>{{ item.item_name }}</h1>
              <p>发布于 {{ formatDate(item.created_at) }}</p>
            </header>

            <div class="action-panel surface-section">
              <template v-if="item.status === 'active'">
                <el-button v-if="canManageItem" type="success" round @click="handleMarkResolved" :loading="actionLoading">
                  <el-icon><CircleCheck /></el-icon>
                  标记为已找回
                </el-button>
                <el-button v-if="!canManageItem" type="primary" plain round @click="handleClaim" :loading="actionLoading">
                  <el-icon><ChatLineRound /></el-icon>
                  {{ claimActionText }}
                </el-button>
              </template>
              <template v-else>
                <el-button v-if="canManageItem" type="warning" round @click="handleMarkPending" :loading="actionLoading">
                  <el-icon><WarningFilled /></el-icon>
                  标记为进行中
                </el-button>
              </template>
            </div>

            <section class="surface-section info-card">
              <h2><el-icon><Document /></el-icon> 物品信息</h2>
              <p class="description">{{ item.description || '发布者未填写详细描述。' }}</p>
              <div class="info-grid">
                <div class="info-row">
                  <el-icon><MapLocation /></el-icon>
                  <span>
                    <small>地点</small>
                    <strong>{{ item.location || '未知地点' }}</strong>
                  </span>
                </div>
                <div class="info-row">
                  <el-icon><Clock /></el-icon>
                  <span>
                    <small>相关时间</small>
                    <strong>{{ item.lost_time ? formatDate(item.lost_time) : '未填写' }}</strong>
                  </span>
                </div>
                <div class="info-row">
                  <el-icon><CollectionTag /></el-icon>
                  <span>
                    <small>分类</small>
                    <strong>{{ item.item_type || '未分类' }}</strong>
                  </span>
                </div>
                <div v-if="canViewContact && item.storage_location" class="info-row">
                  <el-icon><MapLocation /></el-icon>
                  <span>
                    <small>当前存放处</small>
                    <strong>{{ item.storage_location }}</strong>
                  </span>
                </div>
              </div>
            </section>

            <section class="surface-section info-card">
              <h2><el-icon><User /></el-icon> 联系方式</h2>
              <div v-if="canViewContact" class="contact-grid">
                <div class="contact-row">
                  <span>联系人</span>
                  <strong>{{ item.contact_person || '未填写' }}</strong>
                </div>
                <div v-if="item.contact_phone" class="contact-row">
                  <span>电话</span>
                  <strong>{{ item.contact_phone }}</strong>
                </div>
                <div v-if="item.contact_qq" class="contact-row">
                  <span>QQ</span>
                  <strong>{{ item.contact_qq }}</strong>
                </div>
              </div>
              <div v-else class="contact-locked">
                {{ contactLockedText }}
              </div>
            </section>
          </div>
        </section>

        <section v-if="similarItems.length > 0" class="similar-section">
          <div class="section-heading">
            <div>
              <p class="page-kicker">Related</p>
              <h2>相关记录</h2>
            </div>
          </div>
          <el-row :gutter="18">
            <el-col v-for="sim in similarItems" :key="sim.id" :xs="24" :sm="12" :lg="6">
              <article class="data-card sim-card" @click="router.push({ name: 'detail', params: { id: sim.id } })">
                <div class="image-frame sim-image">
                  <img v-if="firstImage(sim.image_url)" :src="resolveImageUrl(firstImage(sim.image_url))" alt="" />
                  <div v-else class="image-placeholder"><el-icon><Picture /></el-icon></div>
                </div>
                <div class="sim-body">
                  <h3>{{ sim.item_name }}</h3>
                  <p><el-icon><MapLocation /></el-icon>{{ sim.location || '未知地点' }}</p>
                  <div class="score-line">
                    <span>匹配度 {{ (sim.similarity * 100).toFixed(0) }}%</span>
                    <el-progress :percentage="sim.similarity * 100" :show-text="false" :stroke-width="5" :color="simColor(sim.similarity)" />
                  </div>
                </div>
              </article>
            </el-col>
          </el-row>
        </section>
      </template>

      <template v-else>
        <div class="surface-section missing-state">
          <el-empty description="没有找到这条记录">
            <el-button type="primary" round @click="goBack">返回</el-button>
          </el-empty>
        </div>
      </template>
    </div>

    <el-dialog v-model="claimDialogVisible" :title="claimDialogTitle" width="520px">
      <div class="claim-content">
        <p>{{ claimDialogNote }}</p>
        <el-form class="claim-form">
          <el-form-item>
            <el-input v-model="claimForm.name" placeholder="您的称呼" size="large">
              <template #prefix><el-icon><User /></el-icon></template>
            </el-input>
          </el-form-item>
          <el-form-item>
            <el-input v-model="claimForm.contact" placeholder="手机号或微信号" size="large">
              <template #prefix><el-icon><Phone /></el-icon></template>
            </el-input>
          </el-form-item>
          <el-form-item>
            <el-input v-model="claimForm.message" type="textarea" :rows="3" placeholder="补充说明，例如物品特征、拾获时间地点或核验信息" />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <div class="dialog-actions">
          <el-button @click="claimDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmClaim" :loading="actionLoading">确认</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft,
  ChatLineRound,
  CircleCheck,
  Clock,
  CollectionTag,
  Document,
  MapLocation,
  Phone,
  Picture,
  PictureFilled,
  User,
  WarningFilled,
} from '@element-plus/icons-vue'
import { lostItemsApi, claimsApi, resolveImageUrl } from '../api'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const route = useRoute()
const router = useRouter()
const item = ref(null)
const loading = ref(true)
const actionLoading = ref(false)
const similarItems = ref([])
const currentImageIndex = ref(0)
const claimDialogVisible = ref(false)
const claimForm = ref({ name: '', contact: '', message: '' })
const myClaims = ref([])

const imageList = computed(() => {
  if (!item.value?.image_url) return []
  return item.value.image_url.split(',').map(v => v.trim()).filter(Boolean)
})

const currentImage = computed(() => {
  if (imageList.value.length === 0) return ''
  return imageList.value[currentImageIndex.value] || imageList.value[0]
})

const canManageItem = computed(() => {
  if (!userStore.isAuthenticated || !item.value) return false
  return userStore.isAdmin || item.value.user_id === userStore.user?.id
})

const hasClaimAccess = computed(() => {
  if (!item.value || !userStore.isAuthenticated) return false
  return myClaims.value.some(claim => claim.item_id === item.value.id)
})

const canViewContact = computed(() => {
  if (!item.value) return false
  if (canManageItem.value || hasClaimAccess.value) return true
  if (item.value.contact_visibility === 'public') return true
  if (item.value.contact_visibility === 'logged_in' && userStore.isAuthenticated) return true
  return false
})

const claimActionText = computed(() => item.value?.direction === 'found' ? '这是我的物品' : '我捡到了，联系失主')
const claimDialogTitle = computed(() => item.value?.direction === 'found' ? '认领确认' : '联系失主')
const claimDialogNote = computed(() => (
  item.value?.direction === 'found'
    ? '请如实填写您的联系方式和核验信息。提交后系统会记录认领并通知发布者。'
    : '请填写您的联系方式和拾获信息。提交后系统会通知失主，由失主与您线下核验。'
))
const contactLockedText = computed(() => {
  if (!userStore.isAuthenticated) return '登录后可申请查看联系方式'
  return item.value?.direction === 'found' ? '请先认领后获取联系方式' : '请先提交联系申请'
})

onMounted(() => {
  loadItem()
})

watch(() => route.params.id, () => {
  loadItem()
})

const loadItem = async () => {
  loading.value = true
  currentImageIndex.value = 0
  try {
    const res = await lostItemsApi.getById(route.params.id)
    item.value = res.data
    await loadMyClaims()
    await loadSimilar()
  } catch (e) {
    item.value = null
    console.error('加载详情失败', e)
  } finally {
    loading.value = false
  }
}

const loadMyClaims = async () => {
  if (!userStore.isAuthenticated) {
    myClaims.value = []
    return
  }
  try {
    const res = await claimsApi.mine()
    myClaims.value = res.data || []
  } catch {
    myClaims.value = []
  }
}

const loadSimilar = async () => {
  if (!item.value) return
  try {
    const oppositeDirection = item.value.direction === 'lost' ? 'found' : 'lost'
    const res = await lostItemsApi.semanticSearch({
      query: `${item.value.item_name} ${item.value.description || ''}`,
      status: 'active',
      direction: oppositeDirection,
      limit: 5,
    })
    similarItems.value = (res.data.results || []).filter(s => s.id !== item.value.id).slice(0, 4)
  } catch (e) {
    similarItems.value = []
    console.error('加载相关记录失败', e)
  }
}

const firstImage = (url) => {
  if (!url) return ''
  return url.split(',').map(v => v.trim()).filter(Boolean)[0] || ''
}

const goBack = () => {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push({ name: 'lost' })
  }
}

const handleMarkResolved = async () => {
  try {
    await ElMessageBox.confirm('确认将这条记录标记为已解决？', '操作确认', {
      type: 'success',
      confirmButtonText: '确认',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }

  actionLoading.value = true
  try {
    await lostItemsApi.update(item.value.id, { status: 'recovered' })
    item.value.status = 'recovered'
    ElMessage.success('已标记为已找回')
  } catch (e) {
    ElMessage.error('操作失败')
  } finally {
    actionLoading.value = false
  }
}

const handleMarkPending = async () => {
  actionLoading.value = true
  try {
    await lostItemsApi.update(item.value.id, { status: 'active' })
    item.value.status = 'active'
    ElMessage.success('已标记为进行中')
  } catch (e) {
    ElMessage.error('操作失败')
  } finally {
    actionLoading.value = false
  }
}

const handleClaim = () => {
  if (!userStore.isAuthenticated) {
    userStore.loginWithCasdoor(`/#${route.fullPath}`)
    return
  }
  claimForm.value = {
    name: userStore.user?.name || '',
    contact: userStore.user?.phone || userStore.user?.qq || userStore.user?.email || '',
    message: '',
  }
  claimDialogVisible.value = true
}

const confirmClaim = async () => {
  if (!claimForm.value.name.trim() || !claimForm.value.contact.trim()) {
    ElMessage.warning('请填写联系信息')
    return
  }
  actionLoading.value = true
  try {
    await claimsApi.create(item.value.id, {
      requester_name: claimForm.value.name,
      requester_contact: claimForm.value.contact,
      message: claimForm.value.message,
    })
    claimDialogVisible.value = false
    ElMessage.success(item.value.direction === 'found' ? '认领已提交，物品已标记为已找回' : '联系申请已提交')
    await loadItem()
  } catch (e) {
    ElMessage.error('操作失败')
  } finally {
    actionLoading.value = false
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '未知'
  return new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const simColor = (score) => {
  if (score >= 0.8) return 'var(--success-color)'
  if (score >= 0.5) return 'var(--warning-color)'
  return 'var(--placeholder-icon-color)'
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
.top-bar {
  margin-bottom: 18px;
}

.skeleton-wrap {
  padding: 24px;
}

.detail-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 430px;
  gap: 18px;
  align-items: start;
}

.gallery-panel {
  padding: 14px;
}

.main-image {
  height: 520px;
  background: var(--media-bg);
}

.main-image-content {
  width: 100%;
  height: 100%;
}

.thumb-row {
  display: flex;
  gap: 10px;
  margin-top: 12px;
  overflow-x: auto;
}

.thumb-button {
  width: 74px;
  height: 74px;
  padding: 0;
  border: 2px solid transparent;
  border-radius: var(--border-radius-md);
  overflow: hidden;
  background: var(--surface-muted);
  cursor: pointer;
  opacity: 0.72;
}

.thumb-button.active {
  border-color: var(--foundit-blue);
  opacity: 1;
}

.thumb-button img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.info-stack {
  display: grid;
  gap: 14px;
}

.item-header {
  padding: 4px 0 2px;
}

.badge-row {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
}

.item-header h1 {
  margin: 0;
  color: var(--text-primary);
  font-size: clamp(28px, 4vw, 38px);
  line-height: 1.18;
  font-weight: 800;
}

.item-header p {
  margin: 10px 0 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.action-panel {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 14px;
}

.info-card {
  padding: 18px;
}

.info-card h2 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 14px;
  font-size: 18px;
  font-weight: 800;
}

.description {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.7;
  white-space: pre-wrap;
}

.info-grid,
.contact-grid {
  display: grid;
  gap: 10px;
  margin-top: 18px;
}

.info-row,
.contact-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-md);
  background: var(--surface-muted);
}

.info-row .el-icon {
  color: var(--foundit-blue);
}

.info-row small,
.info-row strong,
.contact-row span,
.contact-row strong {
  display: block;
}

.info-row small,
.contact-row span {
  color: var(--text-secondary);
  font-size: 12px;
}

.info-row strong,
.contact-row strong {
  margin-top: 3px;
  color: var(--text-primary);
  font-size: 14px;
}

.contact-row {
  justify-content: space-between;
}

.contact-locked {
  margin-top: 18px;
  padding: 16px;
  border: 1px dashed var(--border-color);
  border-radius: var(--border-radius-md);
  background: var(--surface-muted);
  color: var(--text-secondary);
  text-align: center;
  font-weight: 700;
}

.similar-section {
  margin-top: 30px;
}

.section-heading {
  margin-bottom: 14px;
}

.section-heading h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 800;
}

.sim-card {
  margin-bottom: 18px;
}

.sim-image {
  height: 150px;
}

.sim-body {
  padding: 14px;
}

.sim-body h3 {
  margin: 0 0 8px;
  overflow: hidden;
  color: var(--text-primary);
  font-size: 16px;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sim-body p {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  color: var(--text-secondary);
  font-size: 12px;
}

.score-line {
  margin-top: 12px;
}

.score-line span {
  display: block;
  margin-bottom: 6px;
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 800;
}

.missing-state {
  padding: 40px;
}

.claim-content p {
  margin: 0 0 16px;
  color: var(--text-secondary);
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

@media (max-width: 980px) {
  .detail-layout {
    grid-template-columns: 1fr;
  }

  .main-image {
    height: 420px;
  }
}

@media (max-width: 640px) {
  .main-image {
    height: 310px;
  }

  .action-panel {
    display: grid;
  }
}
</style>
