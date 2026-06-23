<template>
  <div class="shell">
    <AppNav />
    <div class="body">
      <!-- 左：世界 / 大纲 / 章节-场景目录 / 人物 -->
      <div class="sidebar">
        <n-select
          :value="store.worldId"
          :options="worldOptions"
          placeholder="选择一个世界"
          @update:value="store.select"
        />

        <template v-if="store.worldId">
          <!-- 剧本大纲（可编辑、可折叠） -->
          <div class="sec">
            <div class="sec__head" @click="showOutline = !showOutline">
              <span>{{ showOutline ? '▾' : '▸' }} 剧本大纲</span>
              <n-button size="tiny" :loading="genning" @click.stop="genOutline">
                {{ store.outline.length ? '重写' : '生成' }}
              </n-button>
            </div>
            <div v-show="showOutline" class="sec__body outline-body">
              <div v-for="(b, i) in editOutline" :key="i" class="ol">
                <div class="ol__row">
                  <span class="ol__no" :class="{ 'ol__no--cur': i === store.beatIndex }">{{ i + 1 }}</span>
                  <n-input v-model:value="b.title" size="tiny" placeholder="章节名" />
                  <n-button size="tiny" text @click="removeBeat(i)">✕</n-button>
                </div>
                <n-input v-model:value="b.goal" size="tiny" type="textarea" :autosize="{ minRows: 1, maxRows: 3 }" placeholder="本章目标/大纲" />
              </div>
              <div class="ol__actions">
                <n-button size="tiny" @click="addBeat">+ 章</n-button>
                <n-button size="tiny" type="primary" @click="saveOutline">保存大纲</n-button>
              </div>
              <div v-if="!editOutline.length" class="hint">点「生成」让编剧写主线，或「+ 章」手动加</div>
            </div>
          </div>

          <!-- 章节 → 场景 两层目录（很多章节时可滚动） -->
          <div class="sec sec--tree">
            <div class="sec__title">章节 / 场景</div>
            <n-scrollbar style="flex:1; min-height:0">
              <div v-for="node in chapterNodes" :key="node.key" class="ch"
                :class="{ 'ch--cur': node.current }">
                <div class="ch__head">
                  <span class="ch__name">{{ node.title }}</span>
                  <span class="ch__cnt">{{ node.scenes.length }}</span>
                  <button class="ch__exp" @click="toggleCh(node.key)">
                    {{ expanded.has(node.key) ? '▾' : '▸' }}
                  </button>
                </div>
                <div v-show="expanded.has(node.key)" class="ch__scenes">
                  <div v-for="s in node.scenes" :key="s.id" class="sc"
                    :class="{ 'sc--active': s.id === store.activeSceneId }"
                    @click="focusScene(s.id)">
                    <span class="sc__dot" :class="s.status === 'active' ? 'sc__dot--on' : ''"></span>
                    {{ s.name }}
                  </div>
                  <div v-if="!node.scenes.length" class="ch__empty">暂无场景</div>
                </div>
              </div>
              <div v-if="!chapterNodes.length" class="hint">先生成或新建章节</div>
            </n-scrollbar>
          </div>

          <!-- 人物 二级菜单（可折叠，点人物看/改细节） -->
          <div class="sec">
            <div class="sec__head" @click="showChars = !showChars">
              <span>{{ showChars ? '▾' : '▸' }} 人物（{{ store.characters.length }}）</span>
            </div>
            <div v-show="showChars" class="sec__body chars">
              <div v-for="c in store.characters" :key="c.id" class="char" @click="store.openChar(c.id)">
                <span class="avatar avatar--sm" :style="{ background: color(c.id) }">{{ first(c.name) }}</span>
                <span class="char__name">{{ c.name }}</span>
                <span class="char__loc">{{ c.location || '—' }}</span>
              </div>
              <div v-if="!store.characters.length" class="hint">还没有角色</div>
            </div>
          </div>
        </template>
      </div>

      <!-- 右：场景对话 + 控制 -->
      <div class="main">
        <template v-if="store.worldId">
          <n-scrollbar class="stage" ref="stageRef">
            <div v-for="s in store.scenes" :key="s.id" :id="'sc-' + s.id" class="scene"
              :class="{ 'scene--active': s.id === store.activeSceneId }">
              <div class="scene__head">
                <span class="scene__day">{{ s.day_label }}</span>
                <span class="scene__name">{{ s.name }}</span>
                <n-tag size="tiny" :type="s.status === 'active' ? 'success' : 'default'" round>
                  {{ s.status === 'active' ? '进行中' : '已结束' }}
                </n-tag>
              </div>
              <div v-if="s.scenario" class="scene__setting">{{ s.scenario }}</div>
              <div v-if="s.collapsed" class="scene__collapsed" @click="store.expandScene(s.id)">
                ▸ 展开本幕对话（{{ s.message_count }} 句）
              </div>
              <div v-else class="dialogue">
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
              <n-button :loading="store.busy" :disabled="store.busy" @click="runScene">
                <template #icon><n-icon><PlayForwardOutline /></n-icon></template>完成本场景
              </n-button>
              <n-button :loading="store.busy" :disabled="store.busy" @click="runChapter">
                <template #icon><n-icon><FlashOutline /></n-icon></template>完成本章
              </n-button>
              <n-button type="primary" :loading="store.busy" :disabled="store.busy" @click="newChapter">
                <template #icon><n-icon><BookOutline /></n-icon></template>新建章节
              </n-button>
              <n-button :disabled="!store.canRollback || store.busy" @click="rollback">
                <template #icon><n-icon><ArrowUndoOutline /></n-icon></template>回退
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

    <!-- 角色详情（可编辑） -->
    <n-drawer v-model:show="store.showChar" :width="430" placement="right">
      <n-drawer-content v-if="store.charDetail" :title="store.charDetail.name" closable>
        <div class="cd">
          <div class="cd__sec">
            <div class="cd__h">基本</div>
            <div class="cd__form">
              <label>状态</label><n-input v-model:value="edit.status" size="small" />
            </div>
            <div v-for="(v, k) in edit.stats" :key="k" class="cd__form">
              <label>{{ statLabel(k) }}</label><n-input-number v-model:value="edit.stats[k]" size="small" :min="0" />
            </div>
            <n-button size="small" type="primary" @click="saveBasic">保存基本</n-button>
          </div>

          <div class="cd__sec">
            <div class="cd__h">心智（情绪/目标/动机/自我认知）</div>
            <div class="cd__form"><label>情绪</label><n-input v-model:value="edit.mood" size="small" /></div>
            <div class="cd__form"><label>目标</label><n-input v-model:value="edit.goals" size="small" type="textarea" :autosize="{ minRows: 1, maxRows: 3 }" /></div>
            <div class="cd__form"><label>动机</label><n-input v-model:value="edit.motivation" size="small" type="textarea" :autosize="{ minRows: 1, maxRows: 3 }" /></div>
            <div class="cd__form"><label>自我认知</label><n-input v-model:value="edit.self_summary" size="small" type="textarea" :autosize="{ minRows: 2, maxRows: 6 }" /></div>
            <n-button size="small" type="primary" @click="saveMental">保存心智</n-button>
          </div>

          <div class="cd__sec">
            <div class="cd__h">长期记忆（印象深刻）</div>
            <div v-if="store.charDetail.long_term.length" class="cd__mems">
              <div v-for="(m, i) in store.charDetail.long_term" :key="i" class="cd__mem">· {{ m.content }}</div>
            </div>
            <div v-else class="cd__empty">（暂无）</div>
          </div>
          <div class="cd__sec">
            <div class="cd__h">短期记忆（最近 5 个场景）</div>
            <div v-if="store.charDetail.short_term.length" class="cd__mems">
              <div v-for="(m, i) in store.charDetail.short_term" :key="i" class="cd__mem">· {{ m.content }}</div>
            </div>
            <div v-else class="cd__empty">（暂无）</div>
          </div>
          <div class="cd__sec" v-if="store.charDetail.relationships.length">
            <div class="cd__h">关系</div>
            <div v-for="(r, i) in store.charDetail.relationships" :key="i" class="cd__rel">
              → {{ r.to }}：{{ r.relation_type }}（好感 {{ r.affinity }}）
            </div>
          </div>
          <div class="cd__sec" v-if="store.charDetail.items.length">
            <div class="cd__h">物品</div>
            <span v-for="(it, i) in store.charDetail.items" :key="i" class="cd__item">{{ it.name }}</span>
          </div>
          <div class="cd__sec" v-if="store.charDetail.abilities.length">
            <div class="cd__h">能力</div>
            <span v-for="(a, i) in store.charDetail.abilities" :key="i" class="cd__item">{{ a.name }} lv{{ a.level }}</span>
          </div>
        </div>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch, nextTick } from 'vue'
import {
  NSelect, NScrollbar, NButton, NInput, NInputNumber, NIcon, NTag,
  NDrawer, NDrawerContent, useMessage,
} from 'naive-ui'
import {
  PlanetOutline, PlayOutline, PlayForwardOutline, FlashOutline,
  ArrowUndoOutline, BookOutline,
} from '@vicons/ionicons5'
import { useStudioStore } from '@/store/Studio'
import AppNav from '@/components/AppNav.vue'

const store = useStudioStore()
const message = useMessage()
const directive = ref('')
const stageRef = ref(null)
const genning = ref(false)

const showOutline = ref(false)
const showChars = ref(true)
const expanded = reactive(new Set())
const toggleCh = (key) => { expanded.has(key) ? expanded.delete(key) : expanded.add(key) }

// 大纲编辑副本
const editOutline = ref([])
watch(() => store.outline, (o) => { editOutline.value = (o || []).map((b) => ({ ...b })) }, { immediate: true, deep: true })
// 只默认展开「当前章节」，避免上百章全展开
watch(() => store.beatIndex, (i) => { expanded.add(`第${(i || 0) + 1}章`) }, { immediate: true })

const addBeat = () => editOutline.value.push({ title: '新章节', goal: '' })
const removeBeat = (i) => editOutline.value.splice(i, 1)
const saveOutline = async () => {
  try { await store.saveOutline(editOutline.value); message.success('大纲已保存') }
  catch (e) { message.error('保存失败') }
}
const genOutline = async () => {
  if (genning.value) return
  genning.value = true
  try { await store.generateOutline(directive.value); message.success('大纲已生成') }
  catch (e) { message.error('生成失败') }
  finally { genning.value = false }
}

// 角色编辑副本
const edit = reactive({ status: '', stats: {}, mood: '', goals: '', motivation: '', self_summary: '' })
watch(() => store.charDetail, (d) => {
  if (!d) return
  edit.status = d.status || ''
  edit.stats = { ...(d.stats || {}) }
  const m = d.mental || {}
  edit.mood = m.mood || ''
  edit.goals = m.goals || ''
  edit.motivation = m.motivation || ''
  edit.self_summary = m.self_summary || ''
})
const saveBasic = async () => {
  try { await store.saveCharBasic(store.charDetail.id, { status: edit.status, stats: edit.stats }); message.success('已保存') }
  catch (e) { message.error('保存失败') }
}
const saveMental = async () => {
  try {
    await store.saveCharMental(store.charDetail.id, {
      mood: edit.mood, goals: edit.goals, motivation: edit.motivation, self_summary: edit.self_summary,
    })
    message.success('已保存')
  } catch (e) { message.error('保存失败') }
}

const worldOptions = computed(() => store.worlds.map((w) => ({ label: w.name, value: w.id })))

// 章节树：由大纲驱动（空章也显示），场景按 day_label 前缀「第N章」归到对应章
const chapterNodes = computed(() => {
  const out = store.outline || []
  const scenes = store.scenes || []
  const matched = new Set()
  const nodes = out.map((b, i) => {
    const prefix = `第${i + 1}章`
    const ss = scenes.filter((s) => (s.day_label || '').startsWith(prefix))
    ss.forEach((s) => matched.add(s.id))
    return { key: prefix, title: `${prefix} ${b.title || ''}`, current: i === store.beatIndex, scenes: ss }
  })
  // 未匹配到任何大纲章的场景（如旧数据）单独成组
  const orphans = scenes.filter((s) => !matched.has(s.id))
  if (orphans.length) nodes.push({ key: '__other__', title: '其它场景', current: false, scenes: orphans })
  return nodes
})

const PALETTE = ['#2563eb', '#dc2626', '#059669', '#d97706', '#7c3aed', '#db2777', '#0891b2', '#65a30d']
const color = (id) => PALETTE[Math.abs(Number(id) || 0) % PALETTE.length]
const nameColor = (name) => {
  let h = 0
  for (const ch of String(name || '')) h = (h * 31 + ch.charCodeAt(0)) % 997
  return PALETTE[h % PALETTE.length]
}
const first = (n) => (n || '?').trim().charAt(0)
const statLabel = (k) => ({ hp: '生命', mp: '法力', stamina: '体力' }[k] || k)

const scrollBottom = () => nextTick(() => stageRef.value?.scrollTo({ position: 'bottom' }))
const focusScene = (id) => {
  const el = document.getElementById('sc-' + id)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
watch(() => store.scenes.map((s) => s.messages.length).join(','), scrollBottom)

const step = async () => {
  try {
    const dir = directive.value
    directive.value = ''
    const timer = setInterval(scrollBottom, 300)
    try { await store.stepStream(dir) } finally { clearInterval(timer) }
    scrollBottom()
  } catch (e) { message.error('推演失败，请重试') }
}
const runScene = async () => {
  try {
    const r = await store.runScene(directive.value); directive.value = ''
    if (r?.data?.success) message.success(`本场景跑了 ${r.data.rounds} 轮`)
    scrollBottom()
  } catch (e) { message.error(e?.code === 'ECONNABORTED' ? '超时，请重试' : '失败，请重试') }
}
const runChapter = async () => {
  try {
    const r = await store.runChapter(directive.value); directive.value = ''
    if (r?.data?.success) message.success(`本章推完：${r.data.scenes} 幕 / ${r.data.rounds} 轮`)
    scrollBottom()
  } catch (e) { message.error(e?.code === 'ECONNABORTED' ? '超时，请重试' : '失败，请重试') }
}
const newChapter = async () => {
  try {
    const r = await store.newChapter(directive.value); directive.value = ''
    if (r?.data?.chapter) message.success(`进入${r.data.chapter}`)
    scrollBottom()
  } catch (e) { message.error('新建章节失败') }
}
const rollback = async () => {
  const r = await store.rollback()
  if (r?.data?.success) message.success('已回退一步')
  else message.error(r?.data?.error || '没有可回退的快照')
}

onMounted(() => store.fetchWorlds())
</script>

<style scoped>
.shell { display: flex; flex-direction: column; height: 100vh; }
.body { flex: 1; display: flex; min-height: 0; }

.sidebar { flex: 0 0 280px; background: var(--c-sidebar); color: var(--c-sidebar-text);
  padding: 14px 12px; display: flex; flex-direction: column; gap: 12px; min-height: 0; }
.sec { display: flex; flex-direction: column; gap: 8px; }
.sec--tree { flex: 1 1 auto; min-height: 0; }
.sec__head { display: flex; align-items: center; justify-content: space-between; font-weight: 600;
  font-size: 14px; cursor: pointer; }
.sec__title { font-weight: 600; font-size: 14px; }
.sec__body { display: flex; flex-direction: column; gap: 8px; }
/* 大纲编辑区有很多章时也能滚 */
.sec__body.outline-body { max-height: 240px; overflow-y: auto; }
.hint { color: #94a3b8; font-size: 12px; }

/* 大纲编辑 */
.ol { background: var(--c-sidebar-soft); border-radius: 8px; padding: 7px 8px; display: flex; flex-direction: column; gap: 5px; }
.ol__row { display: flex; align-items: center; gap: 6px; }
.ol__no { width: 18px; height: 18px; border-radius: 50%; background: rgba(255,255,255,0.12); color: #cbd5e1;
  display: flex; align-items: center; justify-content: center; font-size: 11px; flex: 0 0 auto; }
.ol__no--cur { background: var(--c-primary); color: #fff; }
.ol__actions { display: flex; gap: 8px; }

/* 章节-场景树 */
.ch { margin-bottom: 2px; border-radius: 8px; }
.ch--cur { background: rgba(99,102,241,0.14); }
.ch__head { display: flex; align-items: center; gap: 6px; padding: 6px 6px;
  font-size: 13px; font-weight: 600; }
.ch__name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ch--cur .ch__name { color: #c7d2fe; }
.ch__cnt { font-size: 11px; color: #9aa4b8; }
.ch__exp { border: none; background: rgba(255,255,255,0.08); color: #cbd5e1; cursor: pointer;
  width: 22px; height: 22px; border-radius: 6px; font-size: 12px; flex: 0 0 auto; }
.ch__exp:hover { background: rgba(255,255,255,0.18); }
.ch__scenes { display: flex; flex-direction: column; padding-bottom: 4px; }
.ch__empty { font-size: 11px; color: #6b7280; padding: 3px 4px 3px 22px; }
.sc { display: flex; align-items: center; gap: 6px; padding: 4px 4px 4px 22px; font-size: 12px;
  color: #cbd5e1; cursor: pointer; border-radius: 6px; }
.sc:hover { background: rgba(255,255,255,0.06); }
.sc--active { color: #fff; background: rgba(99,102,241,0.3); }
.sc__dot { width: 6px; height: 6px; border-radius: 50%; background: #6b7280; flex: 0 0 auto; }
.sc__dot--on { background: #22c55e; }

/* 人物菜单 */
.chars { max-height: 220px; overflow-y: auto; }
.char { display: flex; align-items: center; gap: 8px; padding: 6px 6px; border-radius: 8px; cursor: pointer; }
.char:hover { background: var(--c-sidebar-soft); }
.char__name { flex: 1; font-size: 13px; }
.char__loc { font-size: 11px; color: #9aa4b8; }

.main { flex: 1 1 auto; min-width: 0; display: flex; flex-direction: column; background: var(--c-bg); }
.stage { flex: 1; min-height: 0; padding: 20px 28px; }
.scene { background: #fff; border: 1px solid var(--c-border); border-radius: 14px; padding: 14px 18px; margin-bottom: 16px; }
.scene--active { border-color: var(--c-primary); box-shadow: var(--shadow-md); }
.scene__head { display: flex; align-items: center; gap: 10px; }
.scene__day { font-size: 12px; color: var(--c-primary); background: var(--c-primary-soft); padding: 2px 8px; border-radius: 999px; }
.scene__name { font-weight: 700; color: var(--c-text); }
.scene__setting { margin: 8px 0; font-size: 13px; color: var(--c-text-soft); }
.scene__collapsed { color: var(--c-primary); font-size: 13px; cursor: pointer; padding: 6px 0; }
.scene__collapsed:hover { text-decoration: underline; }
.dialogue { display: flex; flex-direction: column; gap: 12px; margin-top: 8px; }
.line { display: flex; gap: 8px; align-items: flex-start; }
.avatar { width: 30px; height: 30px; border-radius: 50%; color: #fff; font-weight: 700; font-size: 13px;
  display: flex; align-items: center; justify-content: center; flex: 0 0 auto; }
.avatar--sm { width: 26px; height: 26px; font-size: 12px; }
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

/* 角色详情抽屉 */
.cd { display: flex; flex-direction: column; gap: 14px; }
.cd__sec { border-top: 1px solid #eef1f5; padding-top: 10px; }
.cd__sec:first-child { border-top: none; padding-top: 0; }
.cd__h { font-size: 13px; font-weight: 700; color: #1e293b; margin-bottom: 8px; }
.cd__form { display: flex; align-items: flex-start; gap: 8px; margin-bottom: 6px; }
.cd__form label { width: 56px; font-size: 12px; color: #64748b; padding-top: 4px; flex: 0 0 auto; }
.cd__form :deep(.n-input), .cd__form :deep(.n-input-number) { flex: 1; }
.cd__mems { display: flex; flex-direction: column; gap: 4px; }
.cd__mem { font-size: 13px; line-height: 1.5; color: #334155; }
.cd__empty { font-size: 12px; color: #94a3b8; }
.cd__rel { font-size: 13px; color: #334155; }
.cd__item { display: inline-block; font-size: 12px; background: #f1f5f9; color: #475569; border-radius: 8px; padding: 2px 10px; margin: 0 6px 6px 0; }
</style>
