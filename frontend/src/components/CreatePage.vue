<template>
  <div class="create-page">
    <div class="form-container glass-card">
      <h2 class="page-title">发布信息</h2>
      <el-steps :active="currentStep" finish-status="success" align-center class="steps-nav clickable-steps">
        <el-step title="基础信息" icon="Edit" @click="currentStep = 0" />
        <el-step title="详情特征" icon="Picture" @click="currentStep = 1" />
        <el-step title="联系方式" icon="User" @click="currentStep = 2" />
      </el-steps>

      <div class="form-wrapper">
        <el-form :model="formData" :rules="rules" ref="formRef" label-position="top">
          <!-- 第一步：基础信息 -->
          <div v-show="currentStep === 0" class="step-content">
            <el-form-item label="信息类型" prop="status">
              <el-radio-group v-model="formData.status" size="large" class="type-selector">
                <el-radio-button value="lost">
                  <div class="radio-content">
                    <el-icon><Warning /></el-icon>
                    <span>我丢了东西 (寻物)</span>
                  </div>
                </el-radio-button>
                <el-radio-button value="found">
                  <div class="radio-content">
                    <el-icon><CircleCheck /></el-icon>
                    <span>我捡到东西 (招领)</span>
                  </div>
                </el-radio-button>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="物品名称" prop="item_name">
              <el-input v-model="formData.item_name" placeholder="请输入核心关键字，如“黑色双肩包”、“校园卡”" size="large" />
            </el-form-item>

            <el-form-item label="物品分类" prop="item_type">
              <el-select v-model="formData.item_type" placeholder="请选择物品分类" size="large" style="width: 100%">
                <el-option label="证件卡片" value="证件卡片" />
                <el-option label="电子产品" value="电子产品" />
                <el-option label="衣物鞋帽" value="衣物鞋帽" />
                <el-option label="学习用品" value="学习用品" />
                <el-option label="钱包钥匙" value="钱包钥匙" />
                <el-option label="其他" value="其他" />
              </el-select>
            </el-form-item>
          </div>

          <!-- 第二步：详情特征 -->
          <div v-show="currentStep === 1" class="step-content">
            <el-form-item label="丢失/拾获地点" prop="location">
              <el-select
                v-model="formData.location"
                placeholder="请选择或输入地点"
                filterable
                allow-create
                default-first-option
                size="large"
                style="width: 100%"
              >
                <el-option v-for="loc in presetLocations" :key="loc" :label="loc" :value="loc" />
              </el-select>
            </el-form-item>

            <el-form-item label="详细特征描述" prop="description">
              <el-input
                type="textarea"
                v-model="formData.description"
                placeholder="请详细描述物品颜色、品牌、特殊标记等特征，越详细越容易被 AI 匹配到"
                :rows="4"
              />
            </el-form-item>

            <el-form-item label="上传图片 (可选，但推荐)">
              <el-upload
                class="image-upload"
                :action="uploadAction"
                :with-credentials="true"
                :before-upload="beforeUpload"
                :on-success="handleUploadSuccess"
                :on-error="handleUploadError"
                :on-remove="handleRemove"
                :file-list="fileList"
                list-type="picture-card"
                :limit="3"
                accept="image/*"
              >
                <div class="upload-trigger">
                  <el-icon size="28"><Plus /></el-icon>
                  <span>添加图片</span>
                </div>
              </el-upload>
              <div class="upload-tip">AI 会自动识别图片内容进行双重匹配，支持最多3张</div>
            </el-form-item>
          </div>

          <!-- 第三步：联系方式 -->
          <div v-show="currentStep === 2" class="step-content">
            <el-form-item label="联系人姓名" prop="contact_person">
              <el-input v-model="formData.contact_person" placeholder="您的称呼，如“王同学”" size="large">
                <template #prefix><el-icon><User /></el-icon></template>
              </el-input>
            </el-form-item>

            <el-form-item label="手机号码" prop="contact_phone">
              <el-input v-model="formData.contact_phone" placeholder="用于平台通知，不会直接公开" size="large">
                <template #prefix><el-icon><Phone /></el-icon></template>
              </el-input>
            </el-form-item>

            <el-form-item label="QQ号码 (可选)" prop="contact_qq">
              <el-input v-model="formData.contact_qq" placeholder="方便拾获者/失主直接联系您" size="large">
                <template #prefix><el-icon><ChatDotRound /></el-icon></template>
              </el-input>
            </el-form-item>
          </div>
        </el-form>

        <div class="form-actions">
          <el-button v-if="currentStep > 0" size="large" @click="prevStep" round>上一步</el-button>
          <el-button v-if="currentStep < 2" type="primary" size="large" @click="nextStep" round>下一步</el-button>
          <el-button v-if="currentStep === 2" type="success" size="large" :loading="submitting" @click="submitForm" round>
            发布信息
          </el-button>
        </div>
      </div>
    </div>

    <!-- Match Check Dialog -->
    <el-dialog v-model="matchDialogVisible" title="疑似匹配结果" width="90%" max-width="600px" destroy-on-close>
      <div class="match-dialog-content">
        <p class="match-tip">我们为您找到了以下疑似匹配的物品，请确认是否有您要找的！</p>
        
        <div v-if="matchResults.length === 0" class="no-match">
          暂未发现高匹配度物品，您可以继续发布。
        </div>
        
        <div v-else class="match-list">
          <div v-for="item in matchResults" :key="item.id" class="match-item">
            <div class="match-item-info">
              <h4>{{ item.item_name }}</h4>
              <p>地点：{{ item.location || '未知' }}</p>
              <div v-if="item.showContact" class="contact-info">
                <p>联系人：{{ item.contact_person }}</p>
                <p v-if="item.contact_phone">电话：{{ item.contact_phone }}</p>
                <p v-if="item.contact_qq">QQ：{{ item.contact_qq }}</p>
              </div>
            </div>
            <div class="match-item-action">
              <el-button v-if="!item.showContact" type="success" size="small" @click="item.showContact = true">
                这就是我要找的！
              </el-button>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="matchDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="finalSubmitting" @click="confirmSubmit">
            都没有我要找的，继续发布
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus, Edit, Picture, User, Phone, ChatDotRound, Warning, CircleCheck } from '@element-plus/icons-vue'
import { apiBase, lostItemsApi } from '../api'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()

const router = useRouter()
const formRef = ref(null)
const currentStep = ref(0)
const submitting = ref(false)
const finalSubmitting = ref(false)
const uploadedUrls = ref([])
const fileList = ref([])
const uploadAction = computed(() => `${apiBase}/api/upload`)

const matchDialogVisible = ref(false)
const matchResults = ref([])

const presetLocations = ['图书馆', '教学楼1号楼', '教学楼2号楼', '教学楼3号楼', '食堂', '宿舍区', '体育馆', '学生活动中心', '其他']

const formData = reactive({
  item_name: '',
  item_type: '',
  description: '',
  location: '',
  lost_time: '',
  status: 'lost',
  image_url: '',
  contact_person: '',
  contact_phone: '',
  contact_qq: ''
})

const rules = {
  item_name: [{ required: true, message: '请输入物品名称', trigger: 'blur' }],
  item_type: [{ required: true, message: '请选择物品分类', trigger: 'change' }],
  location: [{ required: true, message: '请输入丢失/拾获地点', trigger: 'blur' }],
  description: [{ required: true, message: '请输入详细特征', trigger: 'blur' }],
  contact_person: [{ required: true, message: '请输入联系人', trigger: 'blur' }],
  contact_phone: [{ pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }]
}

onMounted(() => {
  if (userStore.user) {
    formData.contact_person = formData.contact_person || userStore.user.name || userStore.user.student_id || ''
    formData.contact_phone = formData.contact_phone || userStore.user.phone || ''
    formData.contact_qq = formData.contact_qq || userStore.user.qq || ''
  }
})

const nextStep = () => {
  if (currentStep.value < 2) currentStep.value++
}

const prevStep = () => {
  currentStep.value--
}

// 把字段名映射到它所在的步骤
const fieldStepMap = {
  item_name: 0, item_type: 0,
  location: 1, description: 1,
  contact_person: 2, contact_phone: 2,
}

const beforeUpload = (file) => {
  const isImage = !file.type || file.type.startsWith('image/')
  if (!isImage) {
    ElMessage.error('只能上传图片文件')
    return false
  }
  if (file.size / 1024 / 1024 > 5) {
    ElMessage.error('图片大小不能超过 5MB')
    return false
  }
  return true
}

const handleUploadSuccess = (response) => {
  if (response.url) {
    uploadedUrls.value.push(response.url)
    formData.image_url = uploadedUrls.value.join(',')
  }
}

const handleUploadError = (err) => {
  ElMessage.error('图片上传失败')
}

const handleRemove = (file) => {
  const url = file.response?.url || file.url
  if (url) {
    uploadedUrls.value = uploadedUrls.value.filter(u => u !== url)
    formData.image_url = uploadedUrls.value.join(',')
  }
}

const submitForm = async () => {
  try {
    await formRef.value.validate()
  } catch (err) {
    // 找到第一个报错的字段，跳转到对应步骤
    const errorFields = Object.keys(err || {})
    for (const key of Object.keys(fieldStepMap)) {
      if (errorFields.includes(key)) {
        currentStep.value = fieldStepMap[key]
        break
      }
    }
    ElMessage.warning('请完善必填信息后提交')
    return
  }

  submitting.value = true
  try {
    const payload = getPayload()
    const matchRes = await lostItemsApi.matchCheck(payload)
    matchResults.value = matchRes.data.results.map(item => ({ ...item, showContact: false }))
    matchDialogVisible.value = true
  } catch (e) {
    ElMessage.error('匹配检查失败，直接进入发布流程')
    confirmSubmit()
  } finally {
    submitting.value = false
  }
}

const getPayload = () => {
  const payload = {}
  for (const [key, value] of Object.entries(formData)) {
    if (value !== '' && value !== null && value !== undefined) {
      payload[key] = value
    }
  }
  return payload
}

const confirmSubmit = async () => {
  finalSubmitting.value = true
  try {
    const payload = getPayload()
    // For new items, we set status to pending in backend automatically,
    // but just in case we let backend handle default status.
    const res = await lostItemsApi.create(payload)
    if (res.status === 200) {
      ElMessage.success('信息发布成功！AI 已记录您的物品特征。')
      matchDialogVisible.value = false
      router.push({ name: 'detail', params: { id: res.data.id } })
    }
  } catch (e) {
    ElMessage.error('发布失败：' + (e.response?.data?.detail || '未知错误'))
  } finally {
    finalSubmitting.value = false
  }
}
</script>

<style scoped>
.create-page {
  padding: 40px 20px;
  min-height: calc(100vh - var(--header-height));
  display: flex;
  justify-content: center;
}

.form-container {
  width: 100%;
  max-width: 680px;
  padding: 40px;
}

.page-title {
  text-align: center;
  font-size: 28px;
  font-weight: 800;
  margin-bottom: 40px;
  color: var(--text-primary);
}

.steps-nav {
  margin-bottom: 40px;
}
.clickable-steps :deep(.el-step__head),
.clickable-steps :deep(.el-step__title) {
  cursor: pointer;
}

.form-wrapper {
  min-height: 400px;
  display: flex;
  flex-direction: column;
}

.step-content {
  flex-grow: 1;
  animation: fadeIn 0.4s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 选项卡式单选框 */
.type-selector {
  width: 100%;
  display: flex;
}
.type-selector :deep(.el-radio-button) {
  flex: 1;
}
.type-selector :deep(.el-radio-button__inner) {
  width: 100%;
  padding: 16px;
  border-radius: var(--border-radius-md) !important;
  border: 1px solid var(--border-color) !important;
  box-shadow: none !important;
  margin-right: 12px;
}
.type-selector :deep(.el-radio-button:last-child .el-radio-button__inner) {
  margin-right: 0;
}
.type-selector :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  border-color: var(--brand-primary) !important;
  background-color: rgba(124, 58, 237, 0.05);
  color: var(--brand-primary);
  box-shadow: 0 0 0 1px var(--brand-primary) !important;
}

.radio-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
}

/* 上传样式 */
.upload-trigger {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
}
.upload-trigger span {
  font-size: 12px;
  margin-top: 8px;
}
.upload-tip {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 8px;
}

.form-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 40px;
  padding-top: 24px;
  border-top: 1px solid var(--border-color);
}
.form-actions .el-button {
  min-width: 120px;
}

/* ===== 响应式 ===== */
@media (max-width: 768px) {
  .create-page {
    padding: 20px 12px;
  }
  .form-container {
    padding: 24px 16px;
  }
  .steps-nav {
    display: none; /* 手机端隐藏步骤条，避免拥挤，可依靠按钮提示 */
  }
  .page-title {
    font-size: 24px;
    margin-bottom: 24px;
  }
}


.match-tip {
  font-weight: bold;
  margin-bottom: 16px;
  color: var(--text-primary);
}
.match-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.match-item {
  border: 1px solid var(--border-color);
  padding: 12px;
  border-radius: var(--border-radius-md);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.match-item-info h4 {
  margin: 0 0 8px 0;
  color: var(--text-primary);
}
.match-item-info p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 14px;
}
.contact-info {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed var(--border-color);
  color: var(--brand-primary) !important;
}
.contact-info p {
  color: var(--brand-primary) !important;
  font-weight: 500;
}
</style>
