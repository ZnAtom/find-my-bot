<template>
  <div class="create-page">
    <div class="page-shell">
      <header class="create-header">
        <div>
          <p class="page-kicker">Create Record</p>
          <h1 class="page-title">{{ pageTitle }}</h1>
          <p class="page-subtitle">{{ pageSubtitle }}</p>
        </div>
      </header>

      <div class="create-layout">
        <aside class="steps-panel surface-section">
          <button
            v-for="(step, index) in steps"
            :key="step.title"
            :class="['step-row', { active: currentStep === index, done: currentStep > index }]"
            type="button"
            @click="currentStep = index"
          >
            <span class="step-index">{{ index + 1 }}</span>
            <span>
              <strong>{{ step.title }}</strong>
              <small>{{ step.desc }}</small>
            </span>
          </button>
        </aside>

        <section class="form-panel surface-section">
          <el-form :model="formData" :rules="rules" ref="formRef" label-position="top">
            <div v-show="currentStep === 0" class="step-content">
              <div class="section-title">
                <h2>基础信息</h2>
                <p>先说明这是一条寻物还是招领记录。</p>
              </div>

              <el-form-item label="信息类型" prop="direction">
                <el-radio-group v-model="formData.direction" class="post-type-grid">
                  <el-radio-button value="lost">
                    <div class="post-type-card">
                      <el-icon><Warning /></el-icon>
                      <strong>我丢了东西</strong>
                      <span>发布寻物记录</span>
                    </div>
                  </el-radio-button>
                  <el-radio-button value="found">
                    <div class="post-type-card">
                      <el-icon><CircleCheck /></el-icon>
                      <strong>我捡到东西</strong>
                      <span>发布招领记录</span>
                    </div>
                  </el-radio-button>
                </el-radio-group>
              </el-form-item>

              <div class="form-grid">
                <el-form-item label="物品名称" prop="item_name">
                  <el-input v-model="formData.item_name" placeholder="例如：黑色双肩包、校园卡、AirPods" size="large" />
                </el-form-item>

                <el-form-item label="物品分类" prop="item_type">
                  <el-select v-model="formData.item_type" placeholder="选择分类" size="large">
                    <el-option v-for="type in itemTypes" :key="type" :label="type" :value="type" />
                  </el-select>
                </el-form-item>
              </div>
            </div>

            <div v-show="currentStep === 1" class="step-content">
              <div class="section-title">
                <h2>详情特征</h2>
                <p>{{ detailStepDescription }}</p>
              </div>

              <div class="form-grid">
                <el-form-item :label="locationLabel" prop="location">
                  <el-select
                    v-model="formData.location"
                    placeholder="选择或输入地点"
                    filterable
                    allow-create
                    default-first-option
                    size="large"
                  >
                    <el-option v-for="loc in presetLocations" :key="loc" :label="loc" :value="loc" />
                  </el-select>
                </el-form-item>

                <el-form-item :label="timeLabel">
                  <el-date-picker
                    v-model="formData.lost_time"
                    type="datetime"
                    placeholder="选择时间"
                    size="large"
                    style="width: 100%"
                    value-format="YYYY-MM-DDTHH:mm:ss"
                  />
                </el-form-item>
              </div>

              <el-form-item v-if="isFound" label="现在存放处" prop="storage_location">
                <el-input v-model="formData.storage_location" placeholder="例如：已交到图书馆前台、暂存在二教门卫处" size="large" />
              </el-form-item>

              <el-form-item label="详细特征" prop="description">
                <el-input
                  type="textarea"
                  v-model="formData.description"
                  placeholder="颜色、品牌、外观、特殊标记、最后出现的位置等"
                  :rows="5"
                />
              </el-form-item>

              <el-form-item label="图片">
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
                <div class="field-tip">最多 3 张，单张不超过 5MB。</div>
              </el-form-item>
            </div>

            <div v-show="currentStep === 2" class="step-content">
              <div class="section-title">
                <h2>联系方式</h2>
                <p>{{ contactStepDescription }}</p>
              </div>

              <el-checkbox v-if="isFound" v-model="leaveContact" size="large" @change="handleLeaveContactChange">
                我想留下联系方式，方便失主联系我
              </el-checkbox>

              <el-alert
                v-if="isFound && !leaveContact"
                title="匿名发布不会绑定账号，发布后不能自行编辑或删除。失主仍可通过认领流程完成归还。"
                type="info"
                show-icon
                :closable="false"
                class="anonymous-note"
              />

              <div v-if="contactFieldsVisible" class="form-grid">
                <el-form-item label="联系人姓名" prop="contact_person">
                  <el-input v-model="formData.contact_person" placeholder="例如：王同学" size="large">
                    <template #prefix><el-icon><User /></el-icon></template>
                  </el-input>
                </el-form-item>

                <el-form-item label="手机号码" prop="contact_phone">
                  <el-input v-model="formData.contact_phone" placeholder="用于联系，不会用于其它用途" size="large">
                    <template #prefix><el-icon><Phone /></el-icon></template>
                    <template #append>
                      <el-button :disabled="!userStore.user?.phone" @click="fillFromProfile('contact_phone', 'phone')">自动填写</el-button>
                    </template>
                  </el-input>
                </el-form-item>
              </div>

              <el-form-item v-if="contactFieldsVisible" label="QQ 号码">
                <el-input v-model="formData.contact_qq" placeholder="可选" size="large">
                  <template #prefix><el-icon><ChatDotRound /></el-icon></template>
                  <template #append>
                    <el-button :disabled="!userStore.user?.qq" @click="fillFromProfile('contact_qq', 'qq')">自动填写</el-button>
                  </template>
                </el-input>
              </el-form-item>

              <el-form-item v-if="contactFieldsVisible" label="邮箱" prop="contact_email">
                <el-input v-model="formData.contact_email" placeholder="可选" size="large">
                  <template #prefix><el-icon><Message /></el-icon></template>
                  <template #append>
                    <el-button :disabled="!userStore.user?.email" @click="fillFromProfile('contact_email', 'email')">自动填写</el-button>
                  </template>
                </el-input>
              </el-form-item>
            </div>
          </el-form>

          <div class="form-actions">
            <el-button v-if="currentStep > 0" round size="large" @click="prevStep">
              上一步
            </el-button>
            <span v-else></span>
            <el-button v-if="currentStep < 2" type="primary" round size="large" @click="nextStep">
              下一步
            </el-button>
            <el-button
              v-else
              type="primary"
              round
              size="large"
              :loading="submitting || finalSubmitting"
              @click="submitForm"
            >
              {{ submitButtonText }}
            </el-button>
          </div>
        </section>
      </div>
    </div>

    <el-dialog v-model="matchDialogVisible" title="疑似匹配结果" width="720px" destroy-on-close>
      <div class="match-dialog-content">
        <p class="match-tip">请先核对以下记录，确认是否已经有人发布了对应物品。</p>

        <div v-if="matchResults.length === 0" class="no-match">
          暂未发现高匹配度记录，可以继续发布。
        </div>

        <div v-else class="match-list">
          <div v-for="item in matchResults" :key="item.id" class="match-item">
            <div class="match-item-info">
              <h4>{{ item.item_name }}</h4>
              <p>{{ item.location || '未知地点' }}</p>
              <div v-if="item.showContact" class="contact-info">
                <p>联系人：{{ item.contact_person || '未填写' }}</p>
                <p v-if="item.contact_phone">电话：{{ item.contact_phone }}</p>
                <p v-if="item.contact_qq">QQ：{{ item.contact_qq }}</p>
                <p v-if="item.contact_email">邮箱：{{ item.contact_email }}</p>
              </div>
            </div>
            <el-button v-if="!item.showContact" type="success" plain round @click="item.showContact = true">
              查看联系方式
            </el-button>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="dialog-actions">
          <el-button @click="matchDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="finalSubmitting" @click="confirmSubmit">
            继续发布
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, reactive, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus, User, Phone, ChatDotRound, Warning, CircleCheck, Message } from '@element-plus/icons-vue'
import { apiBase, lostItemsApi } from '../api'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const router = useRouter()
const route = useRoute()
const formRef = ref(null)
const currentStep = ref(0)
const submitting = ref(false)
const finalSubmitting = ref(false)
const uploadedUrls = ref([])
const fileList = ref([])
const uploadAction = computed(() => `${apiBase}/api/upload`)
const matchDialogVisible = ref(false)
const matchResults = ref([])
const leaveContact = ref(false)

const steps = [
  { title: '基础信息', desc: '类型、名称、分类' },
  { title: '详情特征', desc: '地点、时间、图片' },
  { title: '联系方式', desc: '姓名、手机、QQ/邮箱' },
]

const itemTypes = ['证件卡片', '电子产品', '衣物鞋帽', '学习用品', '钱包钥匙', '其他']
const presetLocations = ['图书馆', '教学楼1号楼', '教学楼2号楼', '教学楼3号楼', '食堂', '宿舍区', '体育馆', '学生活动中心', '其他']

const formData = reactive({
  item_name: '',
  item_type: '',
  description: '',
  location: '',
  storage_location: '',
  lost_time: '',
  direction: 'lost',
  image_url: '',
  contact_person: '',
  contact_phone: '',
  contact_qq: '',
  contact_email: '',
})

const isFound = computed(() => formData.direction === 'found')
const isLost = computed(() => formData.direction === 'lost')
const contactFieldsVisible = computed(() => isLost.value || leaveContact.value)
const pageTitle = computed(() => isFound.value ? '发布招领信息' : '发布寻物信息')
const pageSubtitle = computed(() => (
  isFound.value
    ? '无需登录即可发布招领。填写基础信息和存放处，联系方式可选择是否留下。'
    : '登记丢失物品信息，方便系统匹配和他人联系你。'
))
const detailStepDescription = computed(() => (
  isFound.value
    ? '填写捡到地点、当前存放处和可核对的特征。'
    : '填写丢失地点、时间和详细特征，匹配结果会更准确。'
))
const contactStepDescription = computed(() => (
  isFound.value
    ? '可以匿名发布；如果希望失主直接联系你，需要登录后留下联系方式。'
    : '寻物信息需要至少一种联系方式，默认登录用户可见。'
))
const locationLabel = computed(() => isFound.value ? '捡到地点（选填）' : '丢失地点')
const timeLabel = computed(() => isFound.value ? '捡到时间' : '丢失时间')
const submitButtonText = computed(() => isFound.value ? '发布招领' : '发布寻物')

function isContactRequired() {
  return formData.direction === 'lost' || (formData.direction === 'found' && leaveContact.value)
}

function validateLocation(rule, value, callback) {
  if (formData.direction === 'lost' && !value) {
    callback(new Error('请输入丢失地点'))
    return
  }
  callback()
}

function validateStorageLocation(rule, value, callback) {
  if (formData.direction === 'found' && !value) {
    callback(new Error('请输入当前存放处'))
    return
  }
  callback()
}

function validateDescription(rule, value, callback) {
  if (formData.direction === 'lost' && !value) {
    callback(new Error('请输入详细特征'))
    return
  }
  callback()
}

function validateContactPerson(rule, value, callback) {
  if (isContactRequired() && !value) {
    callback(new Error('请输入联系人'))
    return
  }
  callback()
}

function validatePhone(rule, value, callback) {
  if (value && !/^1[3-9]\d{9}$/.test(value)) {
    callback(new Error('请输入正确的手机号'))
    return
  }
  callback()
}

function validateEmail(rule, value, callback) {
  if (value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
    callback(new Error('请输入正确的邮箱'))
    return
  }
  callback()
}

const rules = {
  direction: [{ required: true, message: '请选择信息类型', trigger: 'change' }],
  item_name: [{ required: true, message: '请输入物品名称', trigger: 'blur' }],
  item_type: [{ required: true, message: '请选择物品分类', trigger: 'change' }],
  location: [{ validator: validateLocation, trigger: 'change' }],
  storage_location: [{ validator: validateStorageLocation, trigger: 'blur' }],
  description: [{ validator: validateDescription, trigger: 'blur' }],
  contact_person: [{ validator: validateContactPerson, trigger: 'blur' }],
  contact_phone: [{ validator: validatePhone, trigger: 'blur' }],
  contact_email: [{ validator: validateEmail, trigger: 'blur' }],
}

const stepFields = [
  ['direction', 'item_name', 'item_type'],
  ['location', 'storage_location', 'description'],
  ['contact_person', 'contact_phone', 'contact_email'],
]

onMounted(() => {
  if (route.query.type === 'lost' || route.query.type === 'found') {
    formData.direction = route.query.type
  }
  formData.lost_time = currentDateTimeValue()
  if (userStore.user) {
    syncContactFromUser({ onlyName: true })
  }
  enforceLoginForCurrentFlow()
})

watch(() => formData.direction, () => {
  if (formData.direction === 'found') {
    leaveContact.value = false
    clearContactFields({ keepName: Boolean(userStore.user) })
  }
  enforceLoginForCurrentFlow()
  formRef.value?.clearValidate()
})

watch(() => userStore.user, (user) => {
  if (user) syncContactFromUser({ onlyName: !contactFieldsVisible.value })
})

const currentDateTimeValue = () => {
  const now = new Date()
  const offsetMs = now.getTimezoneOffset() * 60 * 1000
  return new Date(now.getTime() - offsetMs).toISOString().slice(0, 19)
}

const enforceLoginForCurrentFlow = () => {
  if (isLost.value && !userStore.isAuthenticated) {
    userStore.loginWithCasdoor(`/#${route.fullPath}`)
  }
}

const handleLeaveContactChange = (value) => {
  if (value && !userStore.isAuthenticated) {
    leaveContact.value = false
    userStore.loginWithCasdoor(`/#${route.fullPath}`)
    return
  }
  if (value) {
    syncContactFromUser()
  } else {
    clearContactFields({ keepName: Boolean(userStore.user) })
  }
  formRef.value?.clearValidate(['contact_person', 'contact_phone', 'contact_email'])
}

const syncContactFromUser = ({ onlyName = false } = {}) => {
  formData.contact_person = formData.contact_person || userStore.user?.name || userStore.user?.student_id || ''
  if (onlyName) return
  formData.contact_phone = formData.contact_phone || userStore.user?.phone || ''
  formData.contact_qq = formData.contact_qq || userStore.user?.qq || ''
  formData.contact_email = formData.contact_email || userStore.user?.email || ''
}

const clearContactFields = ({ keepName = false } = {}) => {
  if (!keepName) formData.contact_person = ''
  formData.contact_phone = ''
  formData.contact_qq = ''
  formData.contact_email = ''
}

const fillFromProfile = (targetField, userField) => {
  const value = userStore.user?.[userField]
  if (!value) {
    ElMessage.warning('个人信息中没有可自动填写的内容')
    return
  }
  formData[targetField] = value
  ElMessage.success('已自动填写')
}

const formatApiError = (error, fallback = '未知错误') => {
  const detail = error?.response?.data?.detail
  if (!detail) return fallback
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map(item => {
        const field = Array.isArray(item.loc) ? item.loc.filter(part => part !== 'body').join('.') : ''
        return field ? `${field}: ${item.msg}` : item.msg
      })
      .filter(Boolean)
      .join('；') || fallback
  }
  if (typeof detail === 'object') {
    return detail.msg || detail.message || JSON.stringify(detail)
  }
  return String(detail)
}

const validateStep = async () => {
  const fields = stepFields[currentStep.value]
  if (!formRef.value || !fields) return true
  try {
    await formRef.value.validateField(fields)
    return true
  } catch {
    return false
  }
}

const nextStep = async () => {
  const ok = await validateStep()
  if (!ok) {
    ElMessage.warning('请先补全当前步骤')
    return
  }
  currentStep.value = Math.min(currentStep.value + 1, 2)
}

const prevStep = () => {
  currentStep.value = Math.max(currentStep.value - 1, 0)
}

const fieldStepMap = {
  direction: 0,
  item_name: 0,
  item_type: 0,
  location: 1,
  description: 1,
  contact_person: 2,
  contact_phone: 2,
  contact_email: 2,
  storage_location: 1,
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

const handleUploadError = () => {
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
  if (isLost.value && !userStore.isAuthenticated) {
    userStore.loginWithCasdoor(`/#${route.fullPath}`)
    return
  }
  if (isFound.value && leaveContact.value && !userStore.isAuthenticated) {
    userStore.loginWithCasdoor(`/#${route.fullPath}`)
    return
  }
  try {
    await formRef.value.validate()
  } catch (err) {
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
  if (isContactRequired() && !formData.contact_phone && !formData.contact_qq && !formData.contact_email) {
    currentStep.value = 2
    ElMessage.warning('请至少填写手机号、QQ 或邮箱中的一种联系方式')
    return
  }

  if (isFound.value && !leaveContact.value) {
    confirmSubmit()
    return
  }

  submitting.value = true
  try {
    const payload = getPayload()
    const matchRes = await lostItemsApi.matchCheck(payload)
    matchResults.value = (matchRes.data.results || []).map(item => ({ ...item, showContact: false }))
    matchDialogVisible.value = true
  } catch (e) {
    ElMessage.warning('匹配检查暂时不可用，将直接发布')
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
  payload.status = 'active'
  if (payload.direction === 'lost') {
    payload.contact_visibility = 'logged_in'
  } else if (payload.direction === 'found' && leaveContact.value) {
    payload.contact_visibility = 'claimed'
  } else if (payload.direction === 'found') {
    payload.contact_visibility = 'private'
    payload.contact_person = '匿名'
    delete payload.contact_phone
    delete payload.contact_qq
    delete payload.contact_email
  }
  return payload
}

const confirmSubmit = async () => {
  finalSubmitting.value = true
  try {
    const res = await lostItemsApi.create(getPayload())
    if (res.status === 200) {
      ElMessage.success('发布成功')
      matchDialogVisible.value = false
      router.push({ name: 'detail', params: { id: res.data.id } })
    }
  } catch (e) {
    ElMessage.error('发布失败：' + formatApiError(e))
  } finally {
    finalSubmitting.value = false
  }
}
</script>

<style scoped>
.create-header {
  margin-bottom: 22px;
}

.create-layout {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  gap: 18px;
  align-items: start;
}

.steps-panel {
  position: sticky;
  top: calc(var(--header-height) + 22px);
  padding: 12px;
}

.step-row {
  width: 100%;
  display: grid;
  grid-template-columns: 34px minmax(0, 1fr);
  gap: 12px;
  padding: 14px;
  border: 1px solid transparent;
  border-radius: var(--border-radius-lg);
  background: transparent;
  color: var(--text-secondary);
  text-align: left;
  cursor: pointer;
}

.step-row + .step-row {
  margin-top: 6px;
}

.step-row.active {
  color: var(--text-primary);
  background: var(--accent-soft-hover);
  border-color: var(--accent-soft-border);
}

.step-row.done .step-index {
  background: var(--foundit-teal);
}

.step-index {
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--foundit-blue);
  color: #fff;
  font-size: 13px;
  font-weight: 800;
}

.step-row strong,
.step-row small {
  display: block;
}

.step-row strong {
  font-size: 14px;
}

.step-row small {
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-tertiary);
}

.form-panel {
  padding: 28px;
}

.section-title {
  margin-bottom: 22px;
}

.section-title h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 800;
}

.section-title p {
  margin: 8px 0 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.post-type-grid {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.post-type-grid :deep(.el-radio-button__inner) {
  width: 100%;
  padding: 0;
  border: 1px solid var(--border-color) !important;
  border-radius: var(--border-radius-lg) !important;
  box-shadow: none !important;
  background: var(--surface-color);
}

.post-type-grid :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  color: var(--foundit-blue);
  background: var(--accent-soft-hover);
  border-color: var(--accent-soft-border) !important;
}

.post-type-card {
  min-height: 122px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.post-type-card .el-icon {
  font-size: 24px;
}

.post-type-card strong {
  font-size: 16px;
}

.post-type-card span {
  color: var(--text-secondary);
  font-size: 12px;
}

.field-tip {
  margin-top: 8px;
  color: var(--text-secondary);
  font-size: 12px;
}

.anonymous-note {
  margin: 14px 0;
}

:deep(.el-input-group__append .el-button) {
  min-width: 72px;
}

.upload-trigger {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
}

.upload-trigger span {
  margin-top: 8px;
  font-size: 12px;
  font-weight: 700;
}

.form-actions {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-top: 22px;
  padding-top: 22px;
  border-top: 1px solid var(--border-color);
}

.match-tip {
  margin: 0 0 16px;
  color: var(--text-secondary);
}

.no-match {
  padding: 18px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  background: var(--surface-muted);
  color: var(--text-secondary);
}

.match-list {
  display: grid;
  gap: 12px;
}

.match-item {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 14px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
}

.match-item h4 {
  margin: 0 0 6px;
  font-size: 16px;
}

.match-item p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 13px;
}

.contact-info {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--border-color);
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

@media (max-width: 900px) {
  .create-layout {
    grid-template-columns: 1fr;
  }

  .steps-panel {
    position: static;
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .step-row + .step-row {
    margin-top: 0;
  }
}

@media (max-width: 680px) {
  .form-panel {
    padding: 20px;
  }

  .steps-panel,
  .form-grid,
  .post-type-grid {
    grid-template-columns: 1fr;
  }

  .match-item {
    flex-direction: column;
  }
}
</style>
