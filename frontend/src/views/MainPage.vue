<template>
  <div class="shell">
    <AppNav />
    <div class="page">
      <div class="drawer-mask" v-show="drawerOpen" @click="drawerOpen = false"></div>
      <div class="panel panel--left" :class="{ 'panel--open': drawerOpen }">
        <dashboard />
      </div>
      <div class="panel panel--right">
        <div class="m-bar mobile-only">
          <button class="m-bar__btn" @click="drawerOpen = true" aria-label="菜单">☰</button>
          <span class="m-bar__title">单人对话</span>
        </div>
        <chat />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import AppNav from '@/components/AppNav.vue'
import Dashboard from '@/components/DashBoard.vue'
import Chat from '@/components/Chat.vue'

const drawerOpen = ref(false)   // 手机端左侧面板抽屉
</script>

<style scoped>
.shell {
  display: flex;
  flex-direction: column;
  height: 100vh;
  height: 100dvh;   /* 手机端用动态视口高度，避免地址栏占高导致底部被截 */
  font-family: 'Poppins', sans-serif;
}
.page {
  display: flex;
  flex: 1;
  width: 100%;
  min-height: 0;
}

.panel {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.panel--left {
  flex: 0 0 20%;
  background-color: #414141;
  color: rgb(203, 203, 203);
}

.panel--right {
  flex: 0 0 80%;
  background-color: #d5d5d5;
  color: #232323;
}

/* 手机端顶栏（汉堡 + 标题） */
.m-bar { display: none; align-items: center; gap: 10px; padding: 8px 12px;
  background: #fff; border-bottom: 1px solid var(--c-border); flex: 0 0 auto; }
.m-bar__btn { border: none; background: var(--c-primary-soft); color: var(--c-primary);
  width: 34px; height: 34px; border-radius: 8px; font-size: 18px; cursor: pointer; flex: 0 0 auto; }
.m-bar__title { font-weight: 600; font-size: 15px; color: var(--c-text); }
.drawer-mask { display: none; position: fixed; inset: var(--nav-h) 0 0 0; background: rgba(15,23,42,0.45); z-index: 29; }

@media (max-width: 768px) {
  .panel--left {
    position: fixed; top: var(--nav-h); left: 0; bottom: 0; flex: none; width: 84vw; max-width: 320px;
    transform: translateX(-100%); transition: transform 0.25s ease; z-index: 30;
    box-shadow: var(--shadow-md); align-items: stretch; justify-content: flex-start;
  }
  .panel--left.panel--open { transform: translateX(0); }
  .drawer-mask { display: block; }
  .panel--right {
    flex: 1 1 auto; width: 100%; min-height: 0;
    flex-direction: column; align-items: stretch; justify-content: flex-start;
  }
  /* 聊天组件填充剩余空间（而非 height:100% 占满整列，否则会把输入栏挤出屏幕） */
  .panel--right :deep(.page) { flex: 1 1 auto; min-height: 0; height: auto; }
}
</style>
