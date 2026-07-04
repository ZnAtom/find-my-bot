<script setup>
import { ref } from 'vue'
import Header from './components/Header.vue'
import HomePage from './components/HomePage.vue'
import LostListPage from './components/LostListPage.vue'
import CreatePage from './components/CreatePage.vue'
import AdminPage from './components/AdminPage.vue'

const currentPage = ref('home')

const navigate = (page) => {
  currentPage.value = page
}
</script>

<template>
  <div class="app-container">
    <Header :active-menu="currentPage" @navigate="navigate" />
    <el-main class="main-content">
      <HomePage v-if="currentPage === 'home'" @navigate="navigate" />
      <LostListPage v-else-if="currentPage === 'lost'" />
      <CreatePage v-else-if="currentPage === 'create'" />
      <AdminPage v-else-if="currentPage === 'admin'" />
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