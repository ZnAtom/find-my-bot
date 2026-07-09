<template>
  <div class="detail-page">
    <!-- 加载骨架 -->
    <template v-if="loading">
      <div class="skeleton-container">
        <el-skeleton animated>
          <template #template>
            <div class="skeleton-header">
              <el-skeleton-item variant="text" style="width: 60%; height: 32px" />
              <el-skeleton-item variant="text" style="width: 80px; height: 24px" />
            </div>
            <el-skeleton-item variant="image" style="width: 100%; height: 360px; border-radius: 12px" />
            <div style="margin-top: 24px">
              <el-skeleton-item variant="text" style="width: 40%" />
              <el-skeleton-item variant="text" style="width: 70%" />
              <el-skeleton-item variant="text" style="width: 55%" />
            </div>
          </template>
        </el-skeleton>
      </div>
    </template>

    <!-- 内容 -->
    <template v-else-if="item">
      <!-- 返回按钮 -->
      <div class="back-bar">
        <el-button text @click="goBack">
          <el-icon><ArrowLeft /></el-icon> 返回列表
        </el-button>
      </div>

      <div class="detail-layout">
        <!-- 左侧：图片 -->
        <div class="detail-gallery">
          <div class="main-image" v-if="imageList.length > 0">
            <el-image
              :src="resolveImageUrl(currentImage)"
              fit="cover"
              :preview-src-list="imageList.map(u => resolveImageUrl(u))"
              :initial-index="currentImageIndex"
              preview-teleported
              style="width: 100%; height: 100%"
            >
              <template #error>
                <div class="image-error">
                  <el-icon size="64" color="#c0c4cc"><Picture /></el-icon>
                  <span>图片加载失败</span>
                </div>
              </template>
            </el-image>
          </div>
          <div class="main-image no-image" v-else>
            <el-icon size="72" color="#c0c4cc"><Picture /></el-icon>
            <span>暂无图片</span>
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
            <h1>{{ item.item_name }}</h1>
            <el-tag
              :type="item.status === 'lost' ? 'danger' : 'success'"
              size="large"
              effect="dark"
              round
            >
              {{ item.status === 'lost' ? '🔍 待找回' : '✅ 已找回' }}
            </el-tag>
          </div>

          <!-- 基本信息卡片 -->
          <el-card class="info-card" shadow="never">
            <template #header><span class="card-title">📋 基本信息</span></template>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="物品类型">
                <el-tag type="primary" size="small">{{ item.item_type || '未分类' }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="地点">
                <el-icon><MapLocation /></el-icon> {{ item.location || '未知' }}
              </el-descriptions-item>
              <el-descriptions-item label="丢失时间">
                {{ formatDate(item.lost_time) }}
              </el-descriptions-item>
              <el-descriptions-item label="发布时间">
                {{ formatDate(item.created_at) }}
              </el-descriptions-item>
              <el-descriptions-item label="详细描述" :span="2">
                <span class="desc-text">{{ item.description || '暂无描述' }}</span>
              </el-descriptions-item>
            </el-descriptions>
          </el-card>

          <!-- 联系方式卡片 -->
          <el-card class="info-card contact-card" shadow="never">
            <template #header><span class="card-title">📞 联系方式</span></template>
            <div class="contact-grid">
              <div class="contact-item">
                <el-icon color="#409EFF"><User /></el-icon>
                <div>
                  <span class="contact-label">联系人</span>
                  <span class="contact-value">{{ item.contact_person || '匿名' }}</span>
                </div>
              </div>
              <div class="contact-item" v-if="item.contact_phone">
                <el-icon color="#67C23A"><Phone /></el-icon>
                <div>
                  <span class="contact-label">电话</span>
                  <span class="contact-value">{{ item.contact_phone }}</span>
                </div>
              </div>
              <div class="contact-item" v-if="item.contact_qq">
                <el-icon color="#409EFF"><ChatDotRound /></el-icon>
                <div>
                  <span class="contact-label">QQ</span>
                  <span class="contact-value">{{ item.contact_qq }}</span>
                </div>
              </div>
            </div>
          </el-card>

          <!-- 操作按钮 -->
          <div class="action-bar">
            <el-button
              v-if="item.status === 'lost'"
              type="success"
              size="large"
              @click="handleMarkFound"
              :loading="actionLoading"
            >
              <el-icon><CircleCheck /></el-icon> 标记为已找回
            </el-button>
            <el-button
              v-if="item.status === 'found'"
              type="warning"
              size="large"
              @click="handleMarkLost"
              :loading="actionLoading"
            >
              <el-icon><WarningFilled /></el-icon> 标记为待找回
            </el-button>
            <el-button
              type="primary"
              size="large"
              plain
              @click="handleClaim"
              :loading="actionLoading"
            >
              <el-icon><Star /></el-icon> 这是我的物品，我要认领
            </el-button>
          </div>
        </div>
      </div>

      <!-- 相似物品推荐 -->
      <div class="similar-section" v-if="similarItems.length > 0">
        <h2>🔗 相似物品推荐</h2>
        <el-row :gutter="16">
          <el-col :xs="12" :sm="8" :md="6" v-for="sim in similarItems" :key="sim.id">
            <el-card class="similar-card" shadow="hover" @click="router.push({ name: 'detail', params: { id: sim.id } })">
              <div class="sim-image">
                <img v-if="sim.image_url" :src="resolveImageUrl(sim.image_url.split(',')[0])" alt="" />
                <el-icon v-else size="36" color="#909399"><Picture /></el-icon>
              </div>
              <div class="sim-info">
                <h4>{{ sim.item_name }}</h4>
                <p>{{ sim.location }}</p>
                <span class="sim-score" :style="{ color: simColor(sim.similarity) }">
                  相似度 {{ (sim.similarity * 100).toFixed(0) }}%
                </span>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </template>

    <!-- 错误状态 -->
    <template v-else>
      <el-result icon="error" title="物品不存在" sub-title="该失物信息可能已被删除">
        <template #extra>
          <el-button type="primary" @click="goBack">返回列表</el-button>
        </template>
      </el-result>
    </template>

    <!-- 认领对话框 -->
    <el-dialog v-model="claimDialogVisible" title="认领确认" width="480px" center>
      <div class="claim-content">
        <el-icon size="48" color="#409EFF"><InfoFilled /></el-icon>
        <p>请确认这是您丢失的物品：<strong>{{ item?.item_name }}</strong></p>
        <p class="claim-note">确认后将通知发布者，请准备好相关证明</p>
        <el-form>
          <el-form-item label="您的姓名">
            <el-input v-model="claimForm.name" placeholder="请输入您的姓名" />
          </el-form-item>
          <el-form-item label="联系方式">
            <el-input v-model="claimForm.contact" placeholder="手机号或QQ号" />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="claimDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmClaim" :loading="actionLoading">确认认领</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft, Picture, MapLocation, User, Phone, ChatDotRound,
  CircleCheck, WarningFilled, Star, InfoFilled,
} from '@element-plus/icons-vue'
import { lostItemsApi, resolveImageUrl } from '../api'

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
    await ElMessageBox.confirm('确认将该物品标记为"已找回"？', '操作确认', { type: 'success' })
  } catch { return }

  actionLoading.value = true
  try {
    await lostItemsApi.update(item.value.id, { status: 'found' })
    item.value.status = 'found'
    ElMessage.success('已标记为"已找回"')
  } catch (e) {
    ElMessage.error('操作失败')
  } finally {
    actionLoading.value = false
  }
}

const handleMarkLost = async () => {
  try {
    await ElMessageBox.confirm('确认将该物品重新标记为"待找回"？', '操作确认', { type: 'warning' })
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
  claimForm.value = { name: '', contact: '' }
  claimDialogVisible.value = true
}

const confirmClaim = async () => {
  if (!claimForm.value.name.trim()) {
    ElMessage.warning('请输入您的姓名')
    return
  }
  actionLoading.value = true
  try {
    // 发送认领通知（标记找回 + 模拟通知）
    await lostItemsApi.update(item.value.id, { status: 'found' })
    item.value.status = 'found'
    claimDialogVisible.value = false
    ElMessage.success('认领成功！请准备好相关证明与发布者联系')
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
  if (score >= 0.8) return '#67C23A'
  if (score >= 0.5) return '#E6A23C'
  return '#909399'
}
</script>

<style scoped>
.detail-page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 20px;
}

.back-bar {
  margin-bottom: 16px;
}

/* 骨架屏 */
.skeleton-container {
  padding: 20px;
}

.skeleton-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

/* 内容布局 */
.detail-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
  margin-bottom: 40px;
}

/* 图片区 */
.detail-gallery {
  position: sticky;
  top: 20px;
  align-self: start;
}

.main-image {
  width: 100%;
  height: 400px;
  border-radius: 12px;
  overflow: hidden;
  background: #f5f7fa;
  border: 1px solid #ebeef5;
}

.main-image.no-image {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #909399;
  font-size: 14px;
}

.image-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 100%;
  color: #909399;
}

.thumbnails {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.thumb {
  width: 64px;
  height: 64px;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  border: 2px solid transparent;
  transition: border-color 0.2s;
}

.thumb.active {
  border-color: #409EFF;
}

.thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 信息区 */
.detail-info {}

.info-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  gap: 16px;
}

.info-header h1 {
  font-size: 28px;
  font-weight: 700;
  margin: 0;
  color: #303133;
}

.info-card {
  margin-bottom: 16px;
}

.card-title {
  font-weight: 600;
  font-size: 15px;
}

.desc-text {
  white-space: pre-wrap;
  line-height: 1.8;
  color: #606266;
}

/* 联系方式 */
.contact-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.contact-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.contact-item > .el-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.contact-label {
  display: block;
  font-size: 12px;
  color: #909399;
}

.contact-value {
  font-size: 15px;
  font-weight: 500;
  color: #303133;
}

/* 操作按钮 */
.action-bar {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 8px;
}

/* 相似物品 */
.similar-section {
  margin-top: 48px;
  padding-top: 32px;
  border-top: 1px solid #ebeef5;
}

.similar-section h2 {
  font-size: 20px;
  margin-bottom: 20px;
}

.similar-card {
  cursor: pointer;
  transition: transform 0.2s;
}

.similar-card:hover {
  transform: translateY(-4px);
}

.sim-image {
  height: 120px;
  background: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 8px;
  margin-bottom: 12px;
}

.sim-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.sim-info h4 {
  font-size: 14px;
  margin-bottom: 4px;
}

.sim-info p {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.sim-score {
  font-size: 12px;
  font-weight: 600;
}

/* 认领对话框 */
.claim-content {
  text-align: center;
}

.claim-content > .el-icon {
  margin-bottom: 16px;
}

.claim-note {
  font-size: 13px;
  color: #909399;
  margin-bottom: 16px;
}

@media (max-width: 768px) {
  .detail-page {
    padding: 12px;
  }

  .detail-layout {
    grid-template-columns: 1fr;
    gap: 20px;
  }

  .detail-gallery {
    position: static;
  }

  .main-image {
    height: 240px;
  }

  .info-header {
    flex-direction: column;
    gap: 8px;
  }

  .info-header h1 {
    font-size: 22px;
  }

  .action-bar {
    flex-direction: column;
  }

  .action-bar .el-button {
    width: 100%;
  }

  .info-card :deep(.el-descriptions) {
    --el-descriptions-item-bordered-label-background: #fafafa;
  }

  .similar-section h2 {
    font-size: 18px;
  }
}
</style>
