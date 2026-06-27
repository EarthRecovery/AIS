<template>
  <div class="nav">
    <div class="nav__brand">
      <img src="/logo.svg" alt="Aistoria" class="nav__logo" />
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

      <!-- 沙盘：真实推演 -->
      <button
        class="tab"
        :class="{ 'tab--active': route.path === '/studio' }"
        @click="$router.push('/studio')"
      >
        <n-icon size="17"><PlanetOutline /></n-icon>
        <span>沙盘</span>
      </button>
    </div>

    <div class="nav__right">
      <n-button v-if="auth.isAdmin" text class="nav-log" @click="openLogs" title="LLM 调用日志（管理员）">
        <template #icon><n-icon><DocumentTextOutline /></n-icon></template>
        日志
      </n-button>
      <n-button text class="logout" @click="logout">
        <template #icon><n-icon><LogOutOutline /></n-icon></template>
        退出
      </n-button>
    </div>

    <!-- 管理员：LLM 调用日志 -->
    <n-modal v-model:show="showLogs" preset="card" title="🔍 LLM 调用日志（仅管理员）" class="logs-modal"
      :style="{ maxWidth: '1120px', width: '96vw' }">
      <div class="logs">
        <div class="logs__bar">
          <n-select size="small" v-model:value="logAgent" :options="logAgentOptions"
            style="width: 150px" @update:value="reloadLogs" />
          <n-button size="small" :loading="logsLoading" @click="reloadLogs">刷新</n-button>
          <span class="logs__total">共 {{ logsTotal }} 条</span>
          <n-button size="small" type="error" ghost @click="doClearLogs">清空</n-button>
        </div>
        <div class="logs__body">
          <div class="logs__list">
            <div v-for="l in logs" :key="l.id" class="logrow"
              :class="{ 'logrow--on': curLog && curLog.id === l.id, 'logrow--err': !l.ok }"
              @click="openLog(l.id)">
              <div class="logrow__top">
                <span class="logrow__agent">{{ l.agent || '—' }}</span>
                <span class="logrow__meta">{{ l.total_tokens ?? '?' }}tok · {{ l.duration_ms ?? '?' }}ms</span>
              </div>
              <div class="logrow__time">{{ fmtTime(l.created_at) }}</div>
              <div class="logrow__prev">{{ l.response_preview || l.error || l.prompt_preview }}</div>
            </div>
            <div v-if="!logs.length" class="logs__empty">（暂无调用记录）</div>
          </div>
          <div class="logs__detail">
            <template v-if="curLog">
              <div class="logd__h">#{{ curLog.id }} · {{ curLog.agent }} · {{ curLog.model }}
                · {{ curLog.total_tokens ?? '?' }} tok · {{ curLog.duration_ms ?? '?' }}ms</div>
              <div class="logd__sec">Prompt</div>
              <pre class="logd__pre">{{ curLog.prompt }}</pre>
              <div class="logd__sec">Response</div>
              <pre class="logd__pre logd__pre--resp">{{ curLog.error ? ('ERROR: ' + curLog.error) : curLog.response }}</pre>
            </template>
            <div v-else class="logs__empty">点击左侧任意一条，查看完整 prompt 与回复</div>
          </div>
        </div>
      </div>
    </n-modal>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NIcon, NButton, NModal, NSelect, useMessage } from 'naive-ui'
import {
  ChatbubbleEllipsesOutline, EarthOutline, PlanetOutline, LogOutOutline,
  DocumentTextOutline,
} from '@vicons/ionicons5'
import { useAuthStore } from '@/store/auth'
import { listLlmLogs, getLlmLog, clearLlmLogs } from '@/api/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const message = useMessage()

const chatModes = [
  { path: '/app', label: '单人对话' },
  { path: '/communication', label: '多人对话' },
]

const isChat = computed(() => chatModes.some((m) => m.path === route.path))

const logout = () => {
  localStorage.removeItem('ais_token')
  router.push('/login')
}

// ===== 管理员：LLM 调用日志 =====
onMounted(() => auth.fetchMe())
const showLogs = ref(false)
const logs = ref([])
const logsTotal = ref(0)
const logsLoading = ref(false)
const logAgent = ref(null)
const curLog = ref(null)
const logAgentOptions = [
  { label: '全部来源', value: null },
  { label: 'keeper 裁判', value: 'keeper' },
  { label: 'narrative 叙事', value: 'narrative' },
  { label: 'writing 写作', value: 'writing' },
  { label: 'actor 角色', value: 'actor' },
  { label: 'director 导演', value: 'director' },
  { label: 'speaker_pick 选人', value: 'speaker_pick' },
  { label: 'summary 摘要', value: 'summary' },
  { label: 'rag', value: 'rag' },
]
const fmtTime = (s) => (s ? new Date(s).toLocaleString() : '')
const reloadLogs = async () => {
  logsLoading.value = true
  try {
    const { data } = await listLlmLogs({ limit: 80, agent: logAgent.value || undefined })
    logs.value = data?.logs || []
    logsTotal.value = data?.total || 0
  } catch (e) { message.error('加载日志失败') }
  finally { logsLoading.value = false }
}
const openLogs = async () => { showLogs.value = true; curLog.value = null; await reloadLogs() }
const openLog = async (id) => {
  try { const { data } = await getLlmLog(id); curLog.value = data }
  catch (e) { message.error('加载详情失败') }
}
const doClearLogs = async () => {
  try { await clearLlmLogs(); logs.value = []; logsTotal.value = 0; curLog.value = null; message.success('已清空') }
  catch (e) { message.error('清空失败') }
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
.nav__logo { width: 26px; height: 26px; border-radius: 7px; display: block; }
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

.nav__right { display: flex; align-items: center; gap: 6px; }
.logout { color: #9aa4b8; }
.logout:hover { color: #fca5a5; }
.nav-log { color: #9aa4b8; }
.nav-log:hover { color: #a5b4fc; }

/* LLM 日志面板 */
.logs { display: flex; flex-direction: column; gap: 10px; }
.logs__bar { display: flex; align-items: center; gap: 10px; }
.logs__total { font-size: 12.5px; color: #64748b; margin-right: auto; }
.logs__empty { padding: 14px; font-size: 13px; color: #94a3b8; }
.logs__body { display: flex; gap: 12px; height: 64vh; }
.logs__list { flex: 0 0 320px; overflow-y: auto; border: 1px solid #e5e7eb; border-radius: 8px; }
.logrow { padding: 8px 10px; border-bottom: 1px solid #f1f5f9; cursor: pointer; }
.logrow:hover { background: #f8fafc; }
.logrow--on { background: #eef2ff; }
.logrow--err { background: #fef2f2; }
.logrow__top { display: flex; justify-content: space-between; align-items: center; }
.logrow__agent { font-size: 12.5px; font-weight: 700; color: #4338ca; }
.logrow__meta { font-size: 11px; color: #94a3b8; }
.logrow__time { font-size: 11px; color: #94a3b8; margin: 1px 0 3px; }
.logrow__prev { font-size: 12px; color: #475569; line-height: 1.5; max-height: 3em; overflow: hidden;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; word-break: break-word; }
.logs__detail { flex: 1 1 auto; overflow-y: auto; border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; }
.logd__h { font-size: 12.5px; font-weight: 700; color: #0f172a; margin-bottom: 8px; }
.logd__sec { font-size: 12px; font-weight: 700; color: #6366f1; margin: 10px 0 4px; }
.logd__pre { white-space: pre-wrap; word-break: break-word; font-size: 12.5px; line-height: 1.6;
  background: #f8fafc; border: 1px solid #eef2f7; border-radius: 6px; padding: 8px 10px;
  color: #1e293b; font-family: ui-monospace, monospace; }
.logd__pre--resp { background: #f0fdf4; border-color: #dcfce7; }

/* 手机适配：隐藏标题文字、标签栏横向滚动、整体更紧凑 */
@media (max-width: 768px) {
  .nav { gap: 8px; padding: 0 8px; }
  .nav__title, .nav__subtitle { display: none; }
  .nav__tabs { gap: 6px; overflow-x: auto; -ms-overflow-style: none; scrollbar-width: none; }
  .nav__tabs::-webkit-scrollbar { display: none; }
  .group { padding: 3px 6px; gap: 4px; flex: 0 0 auto; }
  .group__label { display: none; }
  .seg__btn { padding: 5px 9px; font-size: 12px; }
  .tab { padding: 6px 9px; flex: 0 0 auto; font-size: 13px; }
}
</style>
