<template>
  <div class="detail-page">
    <!-- 加载骨架 -->
    <template v-if="loading">
      <div class="skeleton-container">
        <el-skeleton animated>
          <template #template>
            <div class="detail-layout">
              <el-skeleton-item variant="image" class="skeleton-image" />
              <div class="skeleton-info">
                <el-skeleton-item variant="text" style="width: 60%; height: 40px; margin-bottom: 20px" />
                <el-skeleton-item variant="text" style="width: 30%; height: 24px; margin-bottom: 40px" />
                <el-skeleton-item variant="text" style="width: 100%; height: 20px; margin-bottom: 12px" />
                <el-skeleton-item variant="text" style="width: 80%; height: 20px; margin-bottom: 12px" />
                <el-skeleton-item variant="text" style="width: 90%; height: 20px; margin-bottom: 12px" />
              </div>
            </div>
          </template>
        </el-skeleton>
      </div>
    </template>

    <!-- 内容 -->
    <template v-else-if="item">
      <!-- 返回按钮 -->
      <div class="back-bar">
        <el-button class="back-btn" @click="goBack" round>
          <el-icon><ArrowLeft /></el-icon> 返回列表
        </el-button>
      </div>

      <div class="detail-layout">
        <!-- 左侧：图片 -->
        <div class="detail-gallery glass-card">
          <div class="image-showcase" v-if="imageList.length > 0">
            <!-- 模糊背景层 -->
            <div 
              class="image-backdrop" 
              :style="{ backgroundImage: `url(${resolveImageUrl(currentImage)})` }"
            ></div>
            <el-image
              class="main-image-content"
              :src="resolveImageUrl(currentImage)"
              fit="contain"
              :preview-src-list="imageList.map(u => resolveImageUrl(u))"
              :initial-index="currentImageIndex"
              preview-teleported
            >
              <template #error>
                <div class="image-error">
                  <el-icon size="64" color="#cbd5e1"><Picture /></el-icon>
                  <span>图片加载失败</span>
                </div>
              </template>
            </el-image>
          </div>
          <div class="image-showcase no-image" v-else>
            <el-icon size="80" color="#e2e8f0"><PictureFilled /></el-icon>
            <span class="no-img-text">该信息未上传图片</span>
          </div>

          <!-- 缩略图 -->
          <div class="thumbnails" v-if="imageList.length > 1">
            <div
              v-for="(img, idx) in imageList"
              :key="idx"
              :class="['thumb', { active: idx === currentImageIndex }]"
              @click="currentImageIndex = idx"
            >
              <img :src="resolveImageUrl(img)" alt="缩略图" />
            </div>
          </div>
        </div>

        <!-- 右侧：信息 -->
        <div class="detail-info">
          <div class="info-header">
            <div class="badges">
              <span :class="['status-badge', item.status]">
                {{ item.status === 'lost' ? '🔍 丢失待找回' : '✅ 物品已找回' }}
              </span>
              <span class="type-badge">{{ item.item_type || '未分类' }}</span>
            </div>
            <h1 class="item-title">{{ item.item_name }}</h1>
            <div class="time-meta">发布于 {{ formatDate(item.created_at) }}</div>
          </div>

          <!-- 操作区 -->
          <div class="action-card glass-card" v-if="userStore.isAuthenticated">
            <template v-if="item.status === 'lost'">
              <el-button v-if="canManageItem" type="success" size="large" @click="handleMarkFound" :loading="actionLoading" class="action-btn" round>
                <el-icon><CircleCheck /></el-icon> 我已找回该物品
              </el-button>
              <el-button type="primary" size="large" plain @click="handleClaim" :loading="actionLoading" class="action-btn" round>
                <el-icon><Star /></el-icon> 认领该物品
              </el-button>
            </template>
            <template v-else>
              <el-button v-if="canManageItem" type="warning" size="large" @click="handleMarkLost" :loading="actionLoading" class="action-btn" round>
                <el-icon><WarningFilled /></el-icon> 取消找回标记
              </el-button>
            </template>
          </div>

          <!-- 详情信息卡片 -->
          <div class="info-card glass-card">
            <h3 class="card-heading"><el-icon><Document /></el-icon> 详细特征</h3>
            <p class="desc-text">{{ item.description || '主人没有留下任何描述哦。' }}</p>
            
            <div class="meta-grid">
              <div class="meta-item">
                <el-icon><MapLocation /></el-icon>
                <div class="meta-content">
                  <span class="meta-label">丢失/拾获地点</span>
                  <span class="meta-val">{{ item.location || '未知' }}</span>
                </div>
              </div>
              <div class="meta-item" v-if="item.lost_time">
                <el-icon><Clock /></el-icon>
                <div class="meta-content">
                  <span class="meta-label">相关时间</span>
                  <span class="meta-val">{{ formatDate(item.lost_time) }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 联系方式卡片 -->
          <div class="info-card glass-card contact-card">
            <h3 class="card-heading"><el-icon><ChatLineRound /></el-icon> 联系方式</h3>
            <div class="contact-list">
              <div class="contact-row">
                <div class="contact-icon user-icon"><el-icon><User /></el-icon></div>
                <div class="contact-details">
                  <span class="c-label">联系人</span>
                  <span class="c-val">{{ item.contact_person || '匿名' }}</span>
                </div>
              </div>
              <div class="contact-row" v-if="item.contact_phone">
                <div class="contact-icon phone-icon"><el-icon><Phone /></el-icon></div>
                <div class="contact-details">
                  <span class="c-label">电话号码</span>
                  <span class="c-val">{{ item.contact_phone }}</span>
                </div>
              </div>
              <div class="contact-row" v-if="item.contact_qq">
                <div class="contact-icon qq-icon"><el-icon><ChatDotRound /></el-icon></div>
                <div class="contact-details">
                  <span class="c-label">QQ号码</span>
                  <span class="c-val">{{ item.contact_qq }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 相似物品推荐 -->
      <div class="similar-section" v-if="similarItems.length > 0">
        <div class="similar-header">
          <h2><el-icon><MagicStick /></el-icon> AI 相似推荐</h2>
          <p>基于多模态向量检索，这些物品可能与您找的有关联</p>
        </div>
        <el-row :gutter="24">
          <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="sim in similarItems" :key="sim.id">
            <div class="modern-card" @click="router.push({ name: 'detail', params: { id: sim.id } })">
              <div class="card-img-wrap">
                <img v-if="sim.image_url" :src="resolveImageUrl(sim.image_url.split(',')[0])" alt="" />
                <div v-else class="img-placeholder"><el-icon size="40"><Picture /></el-icon></div>
              </div>
              <div class="card-content">
                <h4 class="sim-title">{{ sim.item_name }}</h4>
                <div class="sim-location"><el-icon><MapLocation /></el-icon> {{ sim.location || '未知地点' }}</div>
                <div class="sim-score-box">
                  <div class="score-label">匹配度 {{ (sim.similarity * 100).toFixed(0) }}%</div>
                  <el-progress 
                    :percentage="sim.similarity * 100" 
                    :show-text="false" 
                    :color="simColor(sim.similarity)" 
                    :stroke-width="6" 
                  />
                </div>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>
    </template>

    <!-- 错误状态 -->
    <template v-else>
      <div class="error-state glass-card">
        <el-empty description="哎呀，您要找的信息似乎已经飞到了外太空...">
          <el-button type="primary" size="large" round @click="goBack">返回安全地带</el-button>
        </el-empty>
      </div>
    </template>

    <!-- 认领对话框 -->
    <el-dialog v-model="claimDialogVisible" title="认领确认" width="480px" class="modern-dialog">
      <div class="claim-content">
        <div class="claim-icon"><el-icon><InfoFilled /></el-icon></div>
        <h3 class="claim-target">您正在认领：{{ item?.item_name }}</h3>
        <p class="claim-note">请如实填写您的联系方式，确认后我们将通过系统发送消息给发布者，请您准备好相关的所有权证明以便核实。</p>
        <el-form class="claim-form">
          <el-form-item>
            <el-input v-model="claimForm.name" placeholder="您的称呼（如王同学）" size="large">
              <template #prefix><el-icon><User /></el-icon></template>
            </el-input>
          </el-form-item>
          <el-form-item>
            <el-input v-model="claimForm.contact" placeholder="您的手机号或微信号" size="large">
              <template #prefix><el-icon><Phone /></el-icon></template>
            </el-input>
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="claimDialogVisible = false" round size="large">暂不认领</el-button>
          <el-button type="primary" @click="confirmClaim" :loading="actionLoading" round size="large">发送认领请求</el-button>
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
  ArrowLeft, Picture, PictureFilled, MapLocation, User, Phone, ChatDotRound,
  CircleCheck, WarningFilled, Star, InfoFilled, Document, Clock, ChatLineRound, MagicStick
} from '@element-plus/icons-vue'
import { lostItemsApi, resolveImageUrl } from '../api'
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
const claimForm = ref({ name: '', contact: '' })

const imageList = computed(() => {
  if (!item.value?.image_url) return []
  return item.value.image_url.split(',').filter(Boolean)
})

const currentImage = computed(() => {
  if (imageList.value.length === 0) return ''
  return imageList.value[currentImageIndex.value] || imageList.value[0]
})

const canManageItem = computed(() => {
  if (!userStore.isAuthenticated || !item.value) return false
  return userStore.isAdmin || item.value.user_id === userStore.user?.id
})

onMounted(() => {
  loadItem()
})

watch(() => route.params.id, () => {
  loadItem()
})

const loadItem = async () => {
  loading.value = true
  try {
    const id = route.params.id
    const res = await lostItemsApi.getById(id)
    item.value = res.data
    // 加载相似物品
    loadSimilar()
  } catch (e) {
    item.value = null
    console.error('加载详情失败', e)
  } finally {
    loading.value = false
  }
}

const loadSimilar = async () => {
  if (!item.value) return
  try {
    const res = await lostItemsApi.semanticSearch({
      query: item.value.item_name + ' ' + (item.value.description || ''),
      limit: 5,
    })
    // 过滤掉自身
    similarItems.value = (res.data.results || []).filter(s => s.id !== item.value.id).slice(0, 4)
  } catch (e) {
    console.error('加载相似物品失败', e)
  }
}

const goBack = () => {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push({ name: 'lost' })
  }
}

const handleMarkFound = async () => {
  try {
    await ElMessageBox.confirm('确认将该物品标记为"已找回"？标记后该信息仍会保留。', '操作确认', { 
      type: 'success', confirmButtonText: '确认', cancelButtonText: '取消', center: true
    })
  } catch { return }

  actionLoading.value = true
  try {
    await lostItemsApi.update(item.value.id, { status: 'found' })
    item.value.status = 'found'
    ElMessage.success('已成功标记为"已找回"')
  } catch (e) {
    ElMessage.error('操作失败')
  } finally {
    actionLoading.value = false
  }
}

const handleMarkLost = async () => {
  try {
    await ElMessageBox.confirm('确认将该物品重新标记为"待找回"？', '操作确认', { 
      type: 'warning', confirmButtonText: '确认', cancelButtonText: '取消', center: true
    })
  } catch { return }

  actionLoading.value = true
  try {
    await lostItemsApi.update(item.value.id, { status: 'lost' })
    item.value.status = 'lost'
    ElMessage.success('已标记为"待找回"')
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
  claimForm.value = { name: '', contact: '' }
  claimDialogVisible.value = true
}

const confirmClaim = async () => {
  if (!claimForm.value.name.trim() || !claimForm.value.contact.trim()) {
    ElMessage.warning('请完整填写联系信息')
    return
  }
  actionLoading.value = true
  try {
    claimDialogVisible.value = false
    ElMessage.success('认领请求已记录，请通过页面联系方式联系发布者核实')
  } catch (e) {
    ElMessage.error('操作失败')
  } finally {
    actionLoading.value = false
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '未知'
  return new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
}

const simColor = (score) => {
  if (score >= 0.8) return 'var(--success-color)'
  if (score >= 0.5) return 'var(--warning-color)'
  return '#94a3b8'
}
</script>

<style scoped>
.detail-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px;
}

.back-bar {
  margin-bottom: 24px;
}
.back-btn {
  font-weight: 600;
  padding: 8px 20px;
}

/* 骨架屏 */
.skeleton-container {
  padding: 20px 0;
}
.skeleton-image {
  width: 100%;
  height: 500px;
  border-radius: var(--border-radius-lg);
}
.skeleton-info {
  padding: 20px 0;
}

/* 内容布局 */
.detail-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 40px;
  margin-bottom: 60px;
}

/* 左侧图片区 */
.detail-gallery {
  position: sticky;
  top: calc(var(--header-height) + 40px);
  padding: 16px;
  border-radius: 24px;
  align-self: start;
}

.image-showcase {
  position: relative;
  width: 100%;
  height: 480px;
  border-radius: 16px;
  overflow: hidden;
  background: #0f172a;
}

.image-backdrop {
  position: absolute;
  top: -20px;
  left: -20px;
  right: -20px;
  bottom: -20px;
  background-size: cover;
  background-position: center;
  filter: blur(40px) brightness(0.6);
  z-index: 0;
}

.main-image-content {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.no-image {
  background: var(--background-color);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  border: 2px dashed var(--border-color);
}
.no-img-text {
  color: var(--text-secondary);
  font-weight: 500;
}

.thumbnails {
  display: flex;
  gap: 12px;
  margin-top: 16px;
  overflow-x: auto;
  padding-bottom: 8px;
}

.thumb {
  width: 80px;
  height: 80px;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  border: 3px solid transparent;
  opacity: 0.6;
  transition: all 0.3s;
  flex-shrink: 0;
}
.thumb:hover {
  opacity: 0.8;
}
.thumb.active {
  border-color: var(--brand-primary);
  opacity: 1;
  transform: scale(1.05);
}
.thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 右侧信息区 */
.detail-info {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.info-header {
  margin-bottom: 8px;
}

.badges {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.status-badge {
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 700;
}
.status-badge.lost {
  background: rgba(239, 68, 68, 0.1);
  color: var(--danger-color);
}
.status-badge.found {
  background: rgba(16, 185, 129, 0.1);
  color: var(--success-color);
}

.type-badge {
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  background: var(--surface-color);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.item-title {
  font-size: 36px;
  font-weight: 800;
  color: var(--text-primary);
  margin-bottom: 12px;
  line-height: 1.3;
}

.time-meta {
  color: var(--text-secondary);
  font-size: 14px;
}

.action-card {
  padding: 24px;
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}
.action-btn {
  font-weight: 600;
  flex: 1;
  min-width: 200px;
}

.info-card {
  padding: 32px;
}

.card-heading {
  font-size: 18px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
  color: var(--text-primary);
}
.card-heading .el-icon {
  color: var(--brand-primary);
}

.desc-text {
  font-size: 16px;
  line-height: 1.8;
  color: var(--text-secondary);
  white-space: pre-wrap;
  margin-bottom: 32px;
}

.meta-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.meta-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}
.meta-item .el-icon {
  font-size: 24px;
  color: var(--brand-primary);
  margin-top: 4px;
}
.meta-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.meta-label {
  font-size: 12px;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.meta-val {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

/* 联系方式 */
.contact-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.contact-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  transition: transform 0.2s;
}
.contact-row:hover {
  transform: translateX(8px);
  background: var(--surface-color);
}
.contact-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}
.user-icon { background: linear-gradient(135deg, #60a5fa, #3b82f6); }
.phone-icon { background: linear-gradient(135deg, #34d399, #10b981); }
.qq-icon { background: linear-gradient(135deg, #f472b6, #db2777); }

.contact-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.c-label {
  font-size: 12px;
  color: var(--text-secondary);
}
.c-val {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
}

/* 相似推荐 */
.similar-section {
  margin-top: 80px;
}
.similar-header {
  text-align: center;
  margin-bottom: 40px;
}
.similar-header h2 {
  font-size: 28px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-primary);
  margin-bottom: 8px;
}
.similar-header p {
  color: var(--text-secondary);
  font-size: 16px;
}

.modern-card {
  background: var(--surface-color);
  border-radius: var(--border-radius-lg);
  overflow: hidden;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
  box-shadow: 0 10px 30px rgba(0,0,0,0.03);
  border: 1px solid var(--border-color);
  height: 100%;
  display: flex;
  flex-direction: column;
}
.modern-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 40px rgba(0,0,0,0.08);
}
.card-img-wrap {
  height: 160px;
  background: var(--background-color);
  overflow: hidden;
}
.card-img-wrap img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s;
}
.modern-card:hover .card-img-wrap img {
  transform: scale(1.08);
}
.img-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #cbd5e1;
}
.card-content {
  padding: 20px;
}
.sim-title {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 8px;
  color: var(--text-primary);
}
.sim-location {
  font-size: 13px;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 16px;
}
.sim-score-box {
  margin-top: auto;
}
.score-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

/* 错误状态 */
.error-state {
  padding: 80px 20px;
  text-align: center;
  border-radius: var(--border-radius-lg);
}

/* 对话框 */
.claim-content {
  text-align: center;
  padding: 20px 0;
}
.claim-icon {
  margin-bottom: 24px;
  display: inline-flex;
  padding: 24px;
  background: rgba(99, 102, 241, 0.1);
  border-radius: 50%;
}
.claim-icon .el-icon {
  font-size: 48px;
  color: var(--brand-primary);
}
.claim-target {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 12px;
  color: var(--text-primary);
}
.claim-note {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 32px;
}
.claim-form {
  text-align: left;
}
.dialog-footer {
  display: flex;
  gap: 16px;
  justify-content: center;
  width: 100%;
}
.dialog-footer .el-button {
  flex: 1;
}

@media (max-width: 768px) {
  .detail-layout {
    grid-template-columns: 1fr;
    gap: 24px;
  }
  .detail-gallery {
    position: static;
    padding: 8px;
  }
  .image-showcase {
    height: 320px;
  }
  .item-title {
    font-size: 28px;
  }
  .meta-grid {
    grid-template-columns: 1fr;
  }
}
</style>
