<template>
  <div class="nav">
    <div class="nav__brand">
      <n-icon size="20" class="nav__logo"><SparklesOutline /></n-icon>
      <span class="nav__title">Aistoria</span>
      <span class="nav__subtitle">幻想物语</span>
    </div>

    <div class="nav__tabs">
      <!-- 对话栏目：单人 / 多人 收在一起 -->
      <div class="group" :class="{ 'group--active': isChat }">
        <span class="group__label"><n-icon size="16"><ChatbubbleEllipsesOutline /></n-icon>对话</span>
        <div class="seg">
          <button
            v-for="m in chatModes"
            :key="m.path"
            class="seg__btn"
            :class="{ 'seg__btn--active': route.path === m.path }"
            @click="$router.push(m.path)"
          >{{ m.label }}</button>
        </div>
      </div>

      <!-- 世界管理：独立栏目 -->
      <button
        class="tab"
        :class="{ 'tab--active': route.path === '/world' }"
        @click="$router.push('/world')"
      >
        <n-icon size="17"><EarthOutline /></n-icon>
        <span>世界管理</span>
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
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NIcon, NButton } from 'naive-ui'
import {
  ChatbubbleEllipsesOutline, EarthOutline, SparklesOutline, LogOutOutline,
} from '@vicons/ionicons5'

const route = useRoute()
const router = useRouter()

const chatModes = [
  { path: '/app', label: '单人对话' },
  { path: '/communication', label: '多人对话' },
]

const isChat = computed(() => chatModes.some((m) => m.path === route.path))

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
.nav__title { font-weight: 700; font-size: 16px; letter-spacing: 0.4px; white-space: nowrap; }
.nav__subtitle { font-size: 12px; color: #9aa4b8; white-space: nowrap; }

.nav__tabs { display: flex; align-items: center; gap: 10px; flex: 1; }

/* 对话栏目：标签 + 单人/多人分段开关 */
.group {
  display: flex; align-items: center; gap: 8px;
  padding: 4px 6px 4px 12px; border-radius: 11px;
  border: 1px solid transparent;
}
.group--active { background: rgba(99, 102, 241, 0.12); border-color: rgba(129, 140, 248, 0.35); }
.group__label { display: flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 600; color: #cbd5e1; }
.seg { display: flex; background: rgba(255, 255, 255, 0.06); border-radius: 8px; padding: 2px; }
.seg__btn {
  border: none; background: transparent; cursor: pointer;
  color: #9aa4b8; font-size: 13px; font-weight: 500;
  padding: 5px 12px; border-radius: 6px; transition: background 0.15s, color 0.15s;
}
.seg__btn:hover { color: #e5e7eb; }
.seg__btn--active { color: #fff; background: var(--c-primary); }

.tab {
  display: flex; align-items: center; gap: 7px;
  border: none; background: transparent; cursor: pointer;
  color: #9aa4b8; font-size: 14px; font-weight: 500;
  padding: 8px 14px; border-radius: 9px;
  transition: background 0.15s, color 0.15s;
}
.tab:hover { color: #e5e7eb; background: rgba(255, 255, 255, 0.06); }
.tab--active { color: #fff; background: var(--c-primary); }

.nav__right { display: flex; align-items: center; }
.logout { color: #9aa4b8; }
.logout:hover { color: #fca5a5; }
</style>
