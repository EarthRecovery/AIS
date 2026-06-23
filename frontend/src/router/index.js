import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/store/auth'
import MainPage from '@/views/MainPage.vue'
import AuthView from '@/views/AuthView.vue'
import CommunicationPage from '@/views/CommunicationPage.vue'
import WorldManagePage from '@/views/WorldManagePage.vue'
import StudioPage from '@/views/StudioPage.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/login' },
    { path: '/login', name: 'login', component: AuthView, meta: { guestOnly: true } },
    { path: '/app', name: 'app', component: MainPage, meta: { requiresAuth: true } },
    { path: '/communication', name: 'communication', component: CommunicationPage, meta: { requiresAuth: true } },
    { path: '/world', name: 'world', component: WorldManagePage, meta: { requiresAuth: true } },
    { path: '/studio', name: 'studio', component: StudioPage, meta: { requiresAuth: true } },
    { path: '/:pathMatch(.*)*', redirect: '/login' },
  ],
})

router.beforeEach((to, from, next) => {
  const auth = useAuthStore()
  if (!auth.token) auth.loadFromStorage()

  if (to.meta.requiresAuth && !auth.token) {
    return next({ name: 'login' })
  }
  if (to.meta.guestOnly && auth.token) {
    return next({ name: 'app' })
  }
  return next()
})

export default router
