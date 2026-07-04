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

      <el-form-item label="详细描述" prop="description">
        <el-textarea v-model="formData.description" placeholder="请详细描述物品特征" :rows="4" />
      </el-form-item>

      <el-form-item label="丢失地点" prop="location">
        <el-input v-model="formData.location" placeholder="请输入丢失地点" />
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
import { lostItemsApi } from '../api'

const formRef = ref(null)

const formData = reactive({
  item_name: '',
  item_type: '',
  description: '',
  location: '',
  lost_time: '',
  status: 'lost',
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
    { required: true, message: '请输入联系电话', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ]
}

const submitForm = async () => {
  try {
    await formRef.value.validate()
    const res = await lostItemsApi.create(formData)
    if (res.status === 200) {
      alert('发布成功！')
      resetForm()
    }
  } catch (e) {
    console.error('发布失败', e)
    alert('发布失败，请重试')
  }
}

const resetForm = () => {
  formRef.value.resetFields()
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
</style>