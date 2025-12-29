import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/store/auth'
import MainPage from '@/views/MainPage.vue'
import AuthView from '@/views/AuthView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/login' },
    { path: '/login', name: 'login', component: AuthView, meta: { guestOnly: true } },
    { path: '/app', name: 'app', component: MainPage, meta: { requiresAuth: true } },
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
