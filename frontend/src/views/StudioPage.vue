<template>
  <div class="shell">
    <AppNav />
    <div class="body">
      <!-- 左：世界 + 角色状态 -->
      <div class="sidebar">
        <div class="section">
          <div class="section__title"><n-icon><PlanetOutline /></n-icon> 选择世界</div>
          <n-select
            :value="store.worldId"
            :options="worldOptions"
            placeholder="选择一个世界开始推演"
            @update:value="store.select"
          />
        </div>

        <div v-if="store.world" class="section">
          <div class="section__title"><n-icon><TimeOutline /></n-icon> {{ store.world.in_world_time }}</div>
        </div>

        <div class="section section--chars" v-if="store.worldId">
          <div class="section__title"><n-icon><PeopleOutline /></n-icon> 角色状态</div>
          <n-scrollbar style="flex:1; min-height:0">
            <div v-for="c in store.characters" :key="c.id" class="char">
              <div class="char__head">
                <span class="avatar" :style="{ background: color(c.id) }">{{ first(c.name) }}</span>
                <span class="char__name">{{ c.name }}</span>
                <span class="char__loc">{{ c.location || '未知' }}</span>
              </div>
              <div class="stats">
                <div v-for="(v, k) in c.stats" :key="k" class="stat">
                  <span class="stat__k">{{ statLabel(k) }}</span>
                  <div class="bar"><div class="bar__fill" :style="barStyle(k, v)"></div></div>
                  <span class="stat__v">{{ v }}</span>
                </div>
              </div>
            </div>
            <div v-if="!store.characters.length" class="hint">还没有角色</div>
          </n-scrollbar>
        </div>
      </div>

      <!-- 右：场景对话 + 控制 -->
      <div class="main">
        <template v-if="store.worldId">
          <n-scrollbar class="stage" ref="stageRef">
            <div v-for="s in store.scenes" :key="s.id" class="scene"
              :class="{ 'scene--active': s.id === store.activeSceneId }">
              <div class="scene__head">
                <span class="scene__day">{{ s.day_label }}</span>
                <span class="scene__name">{{ s.name }}</span>
                <n-tag size="tiny" :type="s.status === 'active' ? 'success' : 'default'" round>
                  {{ s.status === 'active' ? '进行中' : '已结束' }}
                </n-tag>
              </div>
              <div v-if="s.scenario" class="scene__setting">{{ s.scenario }}</div>
              <div class="dialogue">
                <div v-for="(m, i) in s.messages" :key="i" class="line">
                  <span class="avatar avatar--sm" :style="{ background: nameColor(m.speaker_name) }">{{ first(m.speaker_name) }}</span>
                  <div class="line__body">
                    <div class="line__name">{{ m.speaker_name }}</div>
                    <div class="line__content">{{ m.content }}</div>
                  </div>
                </div>
                <div v-if="!s.messages.length" class="hint">（尚无对话，点「下一轮」开始）</div>
              </div>
            </div>
            <div v-if="!store.scenes.length" class="empty">
              <n-icon size="44"><PlanetOutline /></n-icon>
              <div>还没有推演。写下（或留空）导演指示，点「下一轮」开始第一幕。</div>
            </div>
          </n-scrollbar>

          <div class="controls">
            <n-input v-model:value="directive" type="textarea" :autosize="{ minRows: 1, maxRows: 4 }"
              placeholder="（可选）导演指示：想让剧情往哪走、引入什么……" />
            <div class="btns">
              <n-button :loading="store.busy" :disabled="store.busy" @click="step">
                <template #icon><n-icon><PlayOutline /></n-icon></template>下一轮
              </n-button>
              <n-button :loading="store.busy" :disabled="store.busy" @click="nextScene">
                <template #icon><n-icon><PlayForwardOutline /></n-icon></template>下一幕
              </n-button>
              <n-button type="primary" :loading="store.busy" :disabled="store.busy" @click="runDay">
                <template #icon><n-icon><FlashOutline /></n-icon></template>自动跑完一天
              </n-button>
              <n-button :disabled="!store.canRollback || store.busy" @click="rollback">
                <template #icon><n-icon><ArrowUndoOutline /></n-icon></template>回退一天
              </n-button>
            </div>
          </div>
        </template>
        <div v-else class="placeholder">
          <n-icon size="46" class="placeholder__icon"><PlanetOutline /></n-icon>
          <div class="placeholder__title">选择一个世界开始推演</div>
          <div class="placeholder__sub">系统会自动建场景、跑对话，每轮结算所有人的状态</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch, nextTick } from 'vue'
import { NSelect, NScrollbar, NButton, NInput, NIcon, NTag, useMessage } from 'naive-ui'
import {
  PlanetOutline, TimeOutline, PeopleOutline, PlayOutline,
  PlayForwardOutline, FlashOutline, ArrowUndoOutline,
} from '@vicons/ionicons5'
import { useStudioStore } from '@/store/Studio'
import AppNav from '@/components/AppNav.vue'

const store = useStudioStore()
const message = useMessage()
const directive = ref('')
const stageRef = ref(null)

const worldOptions = computed(() => store.worlds.map((w) => ({ label: w.name, value: w.id })))

const PALETTE = ['#2563eb', '#dc2626', '#059669', '#d97706', '#7c3aed', '#db2777', '#0891b2', '#65a30d']
const color = (id) => PALETTE[Math.abs(Number(id) || 0) % PALETTE.length]
const nameColor = (name) => {
  let h = 0
  for (const ch of String(name || '')) h = (h * 31 + ch.charCodeAt(0)) % 997
  return PALETTE[h % PALETTE.length]
}
const first = (n) => (n || '?').trim().charAt(0)
const statLabel = (k) => ({ hp: '生命', mp: '法力', stamina: '体力' }[k] || k)
const STAT_COLOR = { hp: '#dc2626', mp: '#2563eb', stamina: '#059669' }
const barStyle = (k, v) => ({
  width: `${Math.max(0, Math.min(100, Number(v) || 0))}%`,
  background: STAT_COLOR[k] || '#6366f1',
})

const scrollBottom = () => nextTick(() => stageRef.value?.scrollTo({ position: 'bottom' }))
watch(() => store.scenes.map((s) => s.messages.length).join(','), scrollBottom)

const step = async () => { await store.step(directive.value); directive.value = ''; scrollBottom() }
const nextScene = async () => { await store.openScene(directive.value); directive.value = '' }
const runDay = async () => {
  const r = await store.runDay(directive.value)
  directive.value = ''
  if (r?.data?.success) message.success(`这一天推完：${r.data.scenes} 幕 / ${r.data.rounds} 轮`)
  scrollBottom()
}
const rollback = async () => {
  const r = await store.rollback()
  if (r?.data?.success) message.success(`已回退到「${r.data.restored_to || '上一天'}」`)
  else message.error(r?.data?.error || '没有可回退的快照')
}

onMounted(() => store.fetchWorlds())
</script>

<style scoped>
.shell { display: flex; flex-direction: column; height: 100vh; }
.body { flex: 1; display: flex; min-height: 0; }

.sidebar { flex: 0 0 280px; background: var(--c-sidebar); color: var(--c-sidebar-text);
  padding: 16px 14px; display: flex; flex-direction: column; gap: 16px; min-height: 0; }
.section { display: flex; flex-direction: column; gap: 8px; }
.section--chars { flex: 1 1 auto; min-height: 0; }
.section__title { display: flex; align-items: center; gap: 6px; font-weight: 600; font-size: 14px; }
.char { background: var(--c-sidebar-soft); border-radius: 10px; padding: 10px 12px; margin-bottom: 8px; }
.char__head { display: flex; align-items: center; gap: 8px; }
.char__name { font-size: 14px; font-weight: 600; flex: 1; }
.char__loc { font-size: 11px; color: #9aa4b8; }
.stats { margin-top: 8px; display: flex; flex-direction: column; gap: 5px; }
.stat { display: flex; align-items: center; gap: 6px; font-size: 11px; }
.stat__k { width: 28px; color: #cbd5e1; }
.stat__v { width: 26px; text-align: right; color: #e5e7eb; }
.bar { flex: 1; height: 6px; background: rgba(255,255,255,0.12); border-radius: 4px; overflow: hidden; }
.bar__fill { height: 100%; border-radius: 4px; transition: width 0.3s; }
.hint { color: #94a3b8; font-size: 12px; }

.main { flex: 1 1 auto; min-width: 0; display: flex; flex-direction: column; background: var(--c-bg); }
.stage { flex: 1; min-height: 0; padding: 20px 28px; }
.scene { background: #fff; border: 1px solid var(--c-border); border-radius: 14px; padding: 14px 18px; margin-bottom: 16px; }
.scene--active { border-color: var(--c-primary); box-shadow: var(--shadow-md); }
.scene__head { display: flex; align-items: center; gap: 10px; }
.scene__day { font-size: 12px; color: var(--c-primary); background: var(--c-primary-soft); padding: 2px 8px; border-radius: 999px; }
.scene__name { font-weight: 700; color: var(--c-text); }
.scene__setting { margin: 8px 0; font-size: 13px; color: var(--c-text-soft); }
.dialogue { display: flex; flex-direction: column; gap: 12px; margin-top: 8px; }
.line { display: flex; gap: 8px; align-items: flex-start; }
.avatar { width: 30px; height: 30px; border-radius: 50%; color: #fff; font-weight: 700; font-size: 13px;
  display: flex; align-items: center; justify-content: center; flex: 0 0 auto; }
.avatar--sm { width: 28px; height: 28px; font-size: 12px; margin-top: 2px; }
.line__name { font-size: 12px; font-weight: 700; color: #475569; margin-bottom: 2px; }
.line__content { white-space: pre-wrap; word-break: break-word; line-height: 1.6; color: #0f172a; }
.empty { height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 10px; color: #94a3b8; text-align: center; }

.controls { flex: 0 0 auto; padding: 14px 24px; background: var(--c-panel); border-top: 1px solid var(--c-border);
  display: flex; flex-direction: column; gap: 10px; }
.btns { display: flex; gap: 10px; flex-wrap: wrap; }
.placeholder { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 6px; }
.placeholder__icon { color: #c7cdd9; }
.placeholder__title { color: var(--c-text-soft); font-size: 16px; font-weight: 600; }
.placeholder__sub { color: var(--c-text-faint); font-size: 13px; }
</style>
