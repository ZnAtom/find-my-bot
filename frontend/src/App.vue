<script setup>
import { onMounted } from 'vue'
import Header from './components/Header.vue'
import auth from './auth'

onMounted(() => {
  auth.restoreSession()
})
</script>

<template>
  <div class="app-container">
    <Header />
    <el-main class="main-content">
      <router-view />
    </el-main>
  </div>
</template>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  padding: 0;
}
</style>
