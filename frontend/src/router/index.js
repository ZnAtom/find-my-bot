import { createRouter, createWebHashHistory } from 'vue-router'
import HomePage from '../components/HomePage.vue'
import LostListPage from '../components/LostListPage.vue'
import CreatePage from '../components/CreatePage.vue'
import AdminPage from '../components/AdminPage.vue'
import DetailPage from '../components/DetailPage.vue'

const routes = [
  { path: '/', name: 'home', component: HomePage },
  { path: '/lost', name: 'lost', component: LostListPage },
  { path: '/lost/:id', name: 'detail', component: DetailPage },
  { path: '/create', name: 'create', component: CreatePage },
  { path: '/admin', name: 'admin', component: AdminPage },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

export default router
