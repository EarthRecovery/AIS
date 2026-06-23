<template>
  <div class="nav">
    <div class="nav__brand">
      <n-icon size="20" class="nav__logo"><SparklesOutline /></n-icon>
      <span class="nav__title">AIS 多智能体世界</span>
    </div>

    <div class="nav__tabs">
      <button
        v-for="t in tabs"
        :key="t.path"
        class="tab"
        :class="{ 'tab--active': isActive(t.path) }"
        @click="$router.push(t.path)"
      >
        <n-icon size="17" class="tab__icon"><component :is="t.icon" /></n-icon>
        <span>{{ t.label }}</span>
      </button>
    </div>

    <div class="nav__right">
      <n-button text class="logout" @click="logout">
        <template #icon><n-icon><LogOutOutline /></n-icon></template>
        退出
      </n-button>
    </div>
  </div>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { NIcon, NButton } from 'naive-ui'
import {
  ChatbubbleEllipsesOutline, PeopleOutline, EarthOutline,
  SparklesOutline, LogOutOutline,
} from '@vicons/ionicons5'

const route = useRoute()
const router = useRouter()

const tabs = [
  { path: '/app', label: '单人对话', icon: ChatbubbleEllipsesOutline },
  { path: '/communication', label: '多人剧场', icon: PeopleOutline },
  { path: '/world', label: '世界管理', icon: EarthOutline },
]

const isActive = (path) => route.path === path

const logout = () => {
  localStorage.removeItem('ais_token')
  router.push('/login')
}
</script>

<style scoped>
.nav {
  height: var(--nav-h);
  flex: 0 0 var(--nav-h);
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 0 20px;
  background: var(--c-sidebar);
  color: #e5e7eb;
  box-shadow: var(--shadow-sm);
  z-index: 10;
}
.nav__brand { display: flex; align-items: center; gap: 8px; }
.nav__logo { color: #a5b4fc; }
.nav__title { font-weight: 700; font-size: 15px; letter-spacing: 0.3px; white-space: nowrap; }

.nav__tabs { display: flex; gap: 6px; flex: 1; }
.tab {
  display: flex; align-items: center; gap: 7px;
  border: none; background: transparent; cursor: pointer;
  color: #9aa4b8; font-size: 14px; font-weight: 500;
  padding: 7px 14px; border-radius: 9px;
  transition: background 0.15s, color 0.15s;
}
.tab:hover { color: #e5e7eb; background: rgba(255, 255, 255, 0.06); }
.tab--active { color: #fff; background: var(--c-primary); }
.tab__icon { display: flex; }

.nav__right { display: flex; align-items: center; }
.logout { color: #9aa4b8; }
.logout:hover { color: #fca5a5; }
</style>
