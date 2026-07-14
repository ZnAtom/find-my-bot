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

        <div class="create-workspace">
          <section class="form-panel surface-section">
            <el-form :model="formData" :rules="rules" ref="formRef" label-position="top">
              <div v-show="currentStep === 0" class="step-content">
                <div class="section-title">
                  <h2>图片识别</h2>
                  <p>先上传图片并识别物品信息，识别结果可继续手动调整。</p>
                </div>

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
                  <div class="field-tip">最多 3 张，单张不超过 5MB。点击识别时，图片会发送至学校图像理解服务，用于自动填写名称、分类和详细特征。</div>
                  <div class="image-analysis-actions">
                    <el-button
                      round
                      :disabled="uploadedUrls.length === 0"
                      :loading="imageAnalyzing"
                      @click="analyzeUploadedImages"
                    >
                      <el-icon><MagicStick /></el-icon>
                      AI智能填信息
                    </el-button>
                  </div>
                </el-form-item>

                <el-form-item prop="direction">
                  <fieldset class="form-fieldset">
                    <legend>信息类型</legend>
                    <el-radio-group v-model="formData.direction" class="post-type-grid" aria-label="信息类型">
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
                  </fieldset>
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

                <el-form-item label="详细特征" prop="description">
                  <el-input
                    type="textarea"
                    v-model="formData.description"
                    placeholder="颜色、品牌、外观、特殊标记等"
                    :rows="5"
                  />
                </el-form-item>
              </div>

              <div v-show="currentStep === 1" class="step-content">
                <div class="section-title">
                  <h2>地点与时间</h2>
                  <p>{{ detailStepDescription }}</p>
                </div>

                <el-form-item :label="locationLabel" prop="location" class="location-form-item">
                  <div class="compact-location-row">
                    <el-cascader
                      v-model="selectedLocationPath"
                      class="location-cascader"
                      :options="campusLocationOptions"
                      :props="locationCascaderProps"
                      filterable
                      clearable
                      :show-all-levels="true"
                      :placeholder="locationSearchPlaceholder"
                      size="large"
                      @change="handleLocationChange"
                    />
                    <el-tooltip
                      content="功能测试中，结果可能不准确，请以手动选择为准"
                      placement="top"
                      :show-after="200"
                    >
                      <el-button class="locate-action" size="large" :loading="locating" @click="handleLocate">
                        <el-icon><Compass /></el-icon>
                        使用当前位置
                      </el-button>
                    </el-tooltip>
                  </div>
                  <div class="field-tip">{{ locationSelectTip }}</div>
                </el-form-item>

                <div :class="['form-grid', { single: !isFound }]">
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

                  <el-form-item v-if="isFound" label="现在存放处" prop="storage_location" required>
                    <el-input v-model="formData.storage_location" placeholder="例如：已交到图书馆前台、暂存在二教门卫处" size="large" />
                  </el-form-item>
                </div>
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

          <aside class="preview-panel surface-section">
            <p class="page-kicker">Live Preview</p>
            <h2>发布预览</h2>
            <article class="record-preview">
              <div class="preview-tags">
                <span :class="['status-chip', isFound ? 'found' : 'lost']">{{ isFound ? '招领中' : '待找回' }}</span>
                <span class="type-chip">{{ formData.item_type || '未选分类' }}</span>
              </div>
              <h3>{{ formData.item_name || '物品名称' }}</h3>
              <p>{{ formData.description || '填写颜色、品牌、外观或特殊标记后，这里会生成发布摘要。' }}</p>
              <div class="preview-meta">
                <span>
                  <el-icon><MapLocation /></el-icon>
                  {{ previewLocation }}
                </span>
                <span>
                  <el-icon><Clock /></el-icon>
                  {{ previewTime }}
                </span>
                <span>
                  <el-icon><Picture /></el-icon>
                  {{ uploadedUrls.length ? `${uploadedUrls.length} 张图片` : '未上传图片' }}
                </span>
                <span>
                  <el-icon><User /></el-icon>
                  {{ previewContactLabel }}
                </span>
              </div>
            </article>

            <div class="readiness-list">
              <div v-for="item in readinessItems" :key="item.label" class="readiness-row">
                <span :class="['readiness-dot', { done: item.done }]"></span>
                <span>{{ item.label }}</span>
              </div>
            </div>
          </aside>
        </div>
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, User, Phone, ChatDotRound, Warning, CircleCheck, Message, MapLocation, Clock, Picture, MagicStick, Compass } from '@element-plus/icons-vue'
import { apiBase, lostItemsApi, uploadApi } from '../api'
import { useUserStore } from '../stores/user'
import {
  campusLocationTree,
  findCampusLocationByPathCodes,
  findNearestCampusLocation,
  formatDistanceMeters,
} from '../data/campusLocations'

const userStore = useUserStore()
const router = useRouter()
const route = useRoute()
const formRef = ref(null)
const currentStep = ref(0)
const submitting = ref(false)
const finalSubmitting = ref(false)
const imageAnalyzing = ref(false)
const uploadedUrls = ref([])
const fileList = ref([])
const uploadAction = computed(() => `${apiBase}/api/upload`)
const matchDialogVisible = ref(false)
const matchResults = ref([])
const leaveContact = ref(false)
const locating = ref(false)
const selectedLocationPath = ref([])

const steps = [
  { title: '图片识别', desc: '图片、名称、分类' },
  { title: '地点与时间', desc: '地点、时间、存放处' },
  { title: '联系方式', desc: '姓名、手机、QQ/邮箱' },
]

const itemTypes = ['证件卡片', '电子产品', '衣物鞋帽', '学习用品', '钱包钥匙', '其他']

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
    ? '无需登录即可发布招领。地点可自动定位，联系方式可选择是否留下。'
    : '登记丢失物品信息，系统会结合地点、时间、图片和描述进行匹配。'
))
const detailStepDescription = computed(() => (
  isFound.value
    ? '选择捡到地点，填写捡到时间和当前存放处。'
    : '选择丢失地点和大致丢失时间，匹配结果会更准确。'
))
const contactStepDescription = computed(() => (
  isFound.value
    ? '可以匿名发布；如果希望失主直接联系你，需要登录后留下联系方式。'
    : '寻物信息需要至少一种联系方式，默认登录用户可见。'
))
const locationLabel = computed(() => isFound.value ? '捡到地点（选填）' : '丢失地点')
const locationSelectTip = computed(() => (
  isFound.value
    ? '捡到地点可留空，但现在存放处为必填。'
    : '可搜索校园地点，也可以使用当前位置自动匹配最近地点。'
))
const locationSearchPlaceholder = computed(() => (
  isFound.value ? '按区域选择或搜索捡到地点' : '按区域选择或搜索丢失地点'
))
const campusLocationOptions = computed(() => campusLocationTree[0]?.children || campusLocationTree)
const locationCascaderProps = {
  value: 'value',
  label: 'label',
  children: 'children',
  emitPath: true,
}
const timeLabel = computed(() => isFound.value ? '捡到时间' : '丢失时间')
const submitButtonText = computed(() => isFound.value ? '发布招领' : '发布寻物')
const contactMethodCount = computed(() => [formData.contact_phone, formData.contact_qq, formData.contact_email].filter(Boolean).length)
const previewLocation = computed(() => (
  isFound.value
    ? (formData.storage_location || formData.location || '待填写现在存放处')
    : (formData.location || '待选择地点')
))
const previewTime = computed(() => formatPreviewTime(formData.lost_time))
const previewContactLabel = computed(() => {
  if (!isContactRequired()) return isFound.value && !leaveContact.value ? '匿名招领' : '联系方式可选'
  if (contactMethodCount.value === 0) return '待填写联系方式'
  return `${contactMethodCount.value} 种联系方式`
})
const readinessItems = computed(() => [
  { label: '图片或物品特征', done: Boolean(uploadedUrls.value.length || formData.description) },
  { label: '类型、名称和分类', done: Boolean(formData.direction && formData.item_name && formData.item_type) },
  { label: isFound.value ? '现在存放处' : '丢失地点', done: isFound.value ? Boolean(formData.storage_location) : Boolean(formData.location) },
  { label: '时间信息', done: Boolean(formData.lost_time) },
  { label: '联系方式设置', done: !isContactRequired() || contactMethodCount.value > 0 },
])

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

function validateDescription(rule, value, callback) {
  if (formData.direction === 'lost' && !value) {
    callback(new Error('请输入详细特征'))
    return
  }
  callback()
}

function validateStorageLocation(rule, value, callback) {
  if (isFound.value && !value) {
    callback(new Error('请输入现在存放处'))
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

const stepFields = computed(() => [
  ['direction', 'item_name', 'item_type', 'description'],
  isFound.value ? ['location', 'storage_location'] : ['location'],
  ['contact_person', 'contact_phone', 'contact_email'],
])

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

const handleLocationChange = (pathCodes = selectedLocationPath.value) => {
  if (!Array.isArray(pathCodes) || pathCodes.length === 0) {
    formData.location = ''
    formRef.value?.clearValidate(['location'])
    return
  }

  const campusCode = campusLocationTree[0]?.value
  const fullPathCodes = campusCode ? [campusCode, ...pathCodes] : pathCodes
  const entry = findCampusLocationByPathCodes(fullPathCodes)
  formData.location = entry?.pathLabel || ''
  formRef.value?.clearValidate(['location'])
}

const applyLocationEntry = (entry) => {
  if (!entry) return
  formData.location = entry.pathLabel || entry.label || ''
  selectedLocationPath.value = Array.isArray(entry.pathCodes) ? entry.pathCodes.slice(1) : []
  formRef.value?.clearValidate(['location'])
}

const handleLocate = () => {
  if (typeof navigator === 'undefined' || !navigator.geolocation) {
    ElMessage.warning('当前浏览器不支持定位，可以手动选择地点')
    return
  }
  if (typeof window !== 'undefined' && !window.isSecureContext) {
    ElMessage.warning('当前位置需要 HTTPS 或 localhost 环境，可以手动选择地点')
    return
  }

  locating.value = true
  navigator.geolocation.getCurrentPosition(
    (position) => {
      locating.value = false
      const coords = [position.coords.longitude, position.coords.latitude]
      const nearest = findNearestCampusLocation(coords)
      if (!nearest) {
        ElMessage.warning('未找到可匹配的校园地点')
        return
      }
      applyLocationEntry(nearest.entry)
      const distanceLabel = formatDistanceMeters(nearest.distanceMeters)
      if (nearest.distanceMeters > 1500) {
        ElMessage.warning(`当前位置离校内地点较远，已填入 ${nearest.entry.label}（约 ${distanceLabel}）`)
      } else {
        ElMessage.success(`已定位到 ${nearest.entry.label}`)
      }
    },
    (error) => {
      locating.value = false
      ElMessage.warning(formatGeoError(error))
    },
    {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 30000,
    },
  )
}

const formatGeoError = (error) => {
  if (error?.code === 1) return '定位权限被拒绝，可以手动选择地点'
  if (error?.code === 2) return '暂时无法获取当前位置，可以手动选择地点'
  if (error?.code === 3) return '定位请求超时，可以手动选择地点'
  return '暂时无法使用当前位置，可以手动选择地点'
}

const formatPreviewTime = (value) => {
  if (!value) return '未选择时间'
  const [date, time = ''] = String(value).split('T')
  if (!date) return value
  return `${date} ${time.slice(0, 5)}`.trim()
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
  const fields = stepFields.value[currentStep.value]
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
  description: 0,
  location: 1,
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

const analysisFields = [
  { key: 'item_name', label: '物品名称' },
  { key: 'item_type', label: '物品分类' },
  { key: 'description', label: '详细特征' },
]

const applyAnalysisResult = (result, overwrite = false) => {
  let applied = 0
  analysisFields.forEach(({ key }) => {
    const value = String(result?.[key] || '').trim()
    if (!value) return
    if (overwrite || !formData[key]) {
      formData[key] = value
      applied += 1
    }
  })

  if (applied > 0) {
    formRef.value?.clearValidate(analysisFields.map(field => field.key))
  }
  return applied
}

const analyzeUploadedImages = async () => {
  if (uploadedUrls.value.length === 0) {
    ElMessage.warning('请先上传图片')
    return
  }

  imageAnalyzing.value = true
  try {
    const res = await uploadApi.analyzeImages(uploadedUrls.value, { silent: true })
    const result = res.data || {}
    const conflictFields = analysisFields
      .filter(({ key }) => String(result[key] || '').trim() && formData[key])
      .map(field => field.label)

    let applied = 0
    if (conflictFields.length > 0) {
      try {
        await ElMessageBox.confirm(
          `识别结果包含已填写的${conflictFields.join('、')}，是否覆盖？`,
          '使用图片识别结果',
          {
            confirmButtonText: '覆盖',
            cancelButtonText: '只填空项',
            type: 'warning',
          }
        )
        applied = applyAnalysisResult(result, true)
      } catch {
        applied = applyAnalysisResult(result, false)
      }
    } else {
      applied = applyAnalysisResult(result, false)
    }

    if (applied > 0) {
      ElMessage.success('已填入图片识别结果')
    } else {
      ElMessage.info('没有可填入的新信息')
    }
  } catch (e) {
    ElMessage.warning(formatApiError(e, '图片识别暂不可用'))
  } finally {
    imageAnalyzing.value = false
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
  grid-template-columns: 260px minmax(0, 1fr);
  gap: 18px;
  align-items: start;
}

.create-layout > * {
  min-width: 0;
}

.create-workspace {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 18px;
  align-items: start;
  min-width: 0;
}

.create-workspace > * {
  min-width: 0;
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
  min-width: 0;
  padding: 28px;
}

.preview-panel {
  min-width: 0;
  position: sticky;
  top: calc(var(--header-height) + 22px);
  padding: 22px;
}

.preview-panel h2 {
  margin: 0 0 16px;
  font-size: 22px;
  font-weight: 800;
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

.form-grid.single {
  grid-template-columns: minmax(0, 1fr);
}

.location-form-item :deep(.el-form-item__content) {
  width: 100%;
}

.compact-location-row {
  width: 100%;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  align-items: start;
}

.location-cascader {
  width: 100%;
}

.locate-action {
  width: 100%;
}

.form-fieldset {
  width: 100%;
  min-width: 0;
  margin: 0;
  padding: 0;
  border: 0;
}

.form-fieldset legend {
  margin: 0 0 8px;
  padding: 0;
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 700;
  line-height: 1.4;
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

.image-analysis-actions {
  margin-top: 10px;
}

.record-preview {
  padding: 16px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  background: var(--surface-muted);
}

.preview-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin-bottom: 14px;
}

.record-preview h3 {
  margin: 0;
  color: var(--text-primary);
  font-size: 20px;
  font-weight: 800;
  line-height: 1.25;
  overflow-wrap: anywhere;
}

.record-preview p {
  margin: 10px 0 0;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.55;
  overflow-wrap: anywhere;
}

.preview-meta {
  display: grid;
  gap: 9px;
  margin-top: 16px;
}

.preview-meta span {
  min-width: 0;
  display: flex;
  gap: 8px;
  align-items: flex-start;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.45;
  overflow-wrap: anywhere;
}

.preview-meta .el-icon {
  margin-top: 2px;
  color: var(--foundit-blue);
  flex: 0 0 auto;
}

.readiness-list {
  display: grid;
  gap: 10px;
  margin-top: 16px;
  padding: 14px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
}

.readiness-row {
  display: flex;
  gap: 9px;
  align-items: center;
  color: var(--text-secondary);
  font-size: 13px;
}

.readiness-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--border-strong);
  flex: 0 0 auto;
}

.readiness-dot.done {
  background: var(--foundit-teal);
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

@media (max-width: 1180px) {
  .create-workspace {
    grid-template-columns: 1fr;
  }

  .preview-panel {
    position: static;
  }
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

  .preview-panel {
    position: static;
  }

  .step-row + .step-row {
    margin-top: 0;
  }
}

@media (max-width: 680px) {
  .form-panel,
  .preview-panel {
    padding: 20px;
  }

  .steps-panel,
  .form-grid,
  .post-type-grid,
  .compact-location-row {
    grid-template-columns: 1fr;
  }

  .compact-location-row .el-button {
    width: 100%;
  }

  .match-item {
    flex-direction: column;
  }
}
</style>
