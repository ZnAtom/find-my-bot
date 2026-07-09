<template>
  <div class="create-page">
    <h2>发布失物信息</h2>
    <el-form :model="formData" :rules="rules" ref="formRef" label-width="120px">
      <el-form-item label="物品名称" prop="item_name">
        <el-input v-model="formData.item_name" placeholder="请输入物品名称" />
      </el-form-item>

      <el-form-item label="物品类型" prop="item_type">
        <el-select v-model="formData.item_type" placeholder="请选择物品类型">
          <el-option label="电子产品" value="电子产品" />
          <el-option label="证件卡片" value="证件卡片" />
          <el-option label="衣物鞋帽" value="衣物鞋帽" />
          <el-option label="学习用品" value="学习用品" />
          <el-option label="其他" value="其他" />
        </el-select>
      </el-form-item>

      <el-form-item label="详细描述">
        <el-input
          type="textarea"
          v-model="formData.description"
          placeholder="请详细描述物品特征"
          :rows="4"
        />
      </el-form-item>

      <el-form-item label="丢失地点" prop="location">
        <el-select
          v-model="formData.location"
          placeholder="请选择或输入地点"
          filterable
          allow-create
          default-first-option
          style="width: 100%"
        >
          <el-option
            v-for="loc in presetLocations"
            :key="loc"
            :label="loc"
            :value="loc"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="丢失时间" prop="lost_time">
        <el-date-picker 
          v-model="formData.lost_time" 
          type="datetime" 
          placeholder="请选择丢失时间"
          value-format="YYYY-MM-DD HH:mm:ss"
        />
      </el-form-item>

      <el-form-item label="当前状态">
        <el-radio-group v-model="formData.status">
          <el-radio value="lost">丢失</el-radio>
          <el-radio value="found">已找回</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="物品图片">
        <el-upload
          action="/api/upload"
          :before-upload="beforeUpload"
          :on-change="handleChange"
          :on-success="handleUploadSuccess"
          :on-error="handleUploadError"
          :on-remove="handleRemove"
          :file-list="fileList"
          list-type="picture-card"
          :limit="3"
          accept="image/*"
        >
          <el-icon><Plus /></el-icon>
        </el-upload>
        <div class="upload-tip">支持 jpg/png/gif/webp，最多 3 张，每张不超过 5MB</div>
      </el-form-item>

      <el-form-item label="联系人" prop="contact_person">
        <el-input v-model="formData.contact_person" placeholder="请输入联系人姓名" />
      </el-form-item>

      <el-form-item label="联系电话" prop="contact_phone">
        <el-input v-model="formData.contact_phone" placeholder="请输入联系电话" />
      </el-form-item>

      <el-form-item label="QQ号码">
        <el-input v-model="formData.contact_qq" placeholder="请输入QQ号码" />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" @click="submitForm">提交发布</el-button>
        <el-button @click="resetForm">重置</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { lostItemsApi } from '../api'

const formRef = ref(null)
const uploadedUrls = ref([])
const fileList = ref([])

const presetLocations = [
  '图书馆',
  '教学楼1号楼',
  '教学楼2号楼',
  '教学楼3号楼',
  '食堂',
  '宿舍区',
  '体育馆',
  '学生活动中心',
  '其他'
]

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
  item_name: [
    { required: true, message: '请输入物品名称', trigger: 'blur' }
  ],
  item_type: [
    { required: true, message: '请选择物品类型', trigger: 'change' }
  ],
  location: [
    { required: true, message: '请输入丢失地点', trigger: 'blur' }
  ],
  contact_person: [
    { required: true, message: '请输入联系人姓名', trigger: 'blur' }
  ],
  contact_phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ]
}

// 上传前校验
const beforeUpload = (file) => {
  // 允许 type 为空的情况（部分浏览器对某些文件类型返回空 MIME）
  const isImage = !file.type || file.type.startsWith('image/')
  if (!isImage) {
    ElMessage.error(`不支持的文件类型: "${file.type}"，只能上传图片文件`)
    return false
  }
  const isLt5M = file.size / 1024 / 1024 < 5
  if (!isLt5M) {
    ElMessage.error(`图片大小 ${(file.size / 1024 / 1024).toFixed(1)}MB 超过 5MB 限制`)
    return false
  }
  // 通过校验，可以看到这条消息说明 beforeUpload 正常
  ElMessage.info(`已选择: ${file.name} (${(file.size / 1024).toFixed(0)}KB)，开始上传...`)
  return true
}

// 文件选择变化（诊断用）
const handleChange = (file, fileListData) => {
  console.log('el-upload change:', file.name, file.status, file.size)
}

// el-upload 上传成功回调
const handleUploadSuccess = (response) => {
  ElMessage.success('图片上传成功')
  if (response.url) {
    uploadedUrls.value.push(response.url)
    formData.image_url = uploadedUrls.value.join(',')
  }
}

// el-upload 上传失败回调
const handleUploadError = (err) => {
  console.error('upload error:', err)
  ElMessage.error('图片上传失败，请检查网络或文件格式')
}

const handleRemove = (file) => {
  // el-upload 的 file 对象中，response 包含我们 onSuccess 时传入的 data
  const url = file.response?.url || file.url
  if (url) {
    uploadedUrls.value = uploadedUrls.value.filter(u => u !== url)
    formData.image_url = uploadedUrls.value.join(',')
  }
}

const submitForm = async () => {
  // 跳过表单验证失败的 catch（Element Plus 会自动显示验证错误）
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  try {
    // 构建提交数据：过滤空字符串，避免 PostgreSQL 解析空字符串报错
    const payload = {}
    for (const [key, value] of Object.entries(formData)) {
      if (value !== '' && value !== null && value !== undefined) {
        payload[key] = value
      }
    }
    const res = await lostItemsApi.create(payload)
    if (res.status === 200) {
      ElMessage.success('发布成功！')
      resetForm()
    }
  } catch (e) {
    if (e.response?.data?.detail) {
      ElMessage.error('发布失败：' + e.response.data.detail)
    } else {
      ElMessage.error('发布失败，请重试')
    }
  }
}

const resetForm = () => {
  formRef.value.resetFields()
  uploadedUrls.value = []
  fileList.value = []
  formData.image_url = ''
}
</script>

<style scoped>
.create-page {
  padding: 40px;
  max-width: 600px;
  margin: 0 auto;
}

.create-page h2 {
  text-align: center;
  margin-bottom: 30px;
  font-size: 24px;
}

.upload-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>