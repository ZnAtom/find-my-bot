import { createRouter, createWebHashHistory } from 'vue-router'
import HomePage from '../components/HomePage.vue'
import LostListPage from '../components/LostListPage.vue'
import CreatePage from '../components/CreatePage.vue'
import AdminPage from '../components/AdminPage.vue'
import DetailPage from '../components/DetailPage.vue'
import ProfilePage from '../components/ProfilePage.vue'
import auth from '../auth'

const routes = [
  { path: '/', name: 'home', component: HomePage, meta: { public: true } },
  { path: '/lost', name: 'lost', component: LostListPage, meta: { public: true } },
  { path: '/lost/:id', name: 'detail', component: DetailPage, meta: { public: true } },
  { path: '/create', name: 'create', component: CreatePage, meta: { requiresAuth: true } },
  { path: '/profile', name: 'profile', component: ProfilePage, meta: { requiresAuth: true } },
  { path: '/admin', name: 'admin', component: AdminPage, meta: { requiresAuth: true, requiresAdmin: true } },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach(async (to) => {
  if (!auth.state.loaded) {
    await auth.restoreSession()
  }

  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    auth.loginWithCasdoor(`/#${to.fullPath}`)
    return false
  }

  if (to.meta.requiresAdmin && !auth.isAdminView) {
    return { name: 'home' }
  }
})

export default router
