<template>
  <div class="shell">
    <AppNav />
    <div class="body">
      <div class="drawer-mask" v-show="drawerOpen" @click="drawerOpen = false"></div>
      <!-- 左：世界 / 大纲 / 章节-场景目录 / 人物 -->
      <div class="sidebar" :class="{ 'sidebar--open': drawerOpen }">
        <n-select
          :value="store.worldId"
          :options="worldOptions"
          placeholder="选择一个世界"
          @update:value="onSelectWorld"
        />
        <n-button block secondary class="set-btn" @click="showGen = true">
          <template #icon><n-icon><SparklesOutline /></n-icon></template>
          ✨ AI 生成新世界
        </n-button>

        <template v-if="store.worldId">
          <!-- 设置 / 大纲：点击弹出浮窗 -->
          <div class="sec">
            <n-button block secondary class="set-btn" @click="showSettings = true">
              <template #icon><n-icon><SettingsOutline /></n-icon></template>
              设置 / 大纲
            </n-button>
          </div>

          <!-- 章节 → 场景 两层目录（很多章节时可滚动） -->
          <div class="sec sec--tree">
            <div class="sec__title">章节 / 场景</div>
            <n-scrollbar style="flex:1; min-height:0">
              <div v-for="node in chapterNodes" :key="node.key" class="ch"
                :class="{ 'ch--cur': node.current }">
                <div class="ch__head">
                  <span class="ch__name" :class="{ 'ch__name--viewing': node.key === focusedKey }"
                    @click="focusChapter(node.key)">{{ node.title }}</span>
                  <span class="ch__cnt">{{ node.scenes.length }}</span>
                  <button class="ch__exp" @click="toggleCh(node.key)">
                    {{ expanded.has(node.key) ? '▾' : '▸' }}
                  </button>
                </div>
                <div v-show="expanded.has(node.key)" class="ch__scenes">
                  <div v-for="s in node.scenes" :key="s.id" class="sc"
                    :class="{ 'sc--active': s.id === store.activeSceneId }"
                    @click="focusScene(s.id, node.key)">
                    <span class="sc__dot" :class="s.status === 'active' ? 'sc__dot--on' : ''"></span>
                    {{ s.name }}
                  </div>
                  <div v-if="!node.scenes.length" class="ch__empty">暂无场景</div>
                </div>
              </div>
              <div v-if="!chapterNodes.length" class="hint">先生成大纲，或点「下一轮」开始第一章</div>
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
        <div class="m-bar mobile-only">
          <button class="m-bar__btn" @click="drawerOpen = true" aria-label="菜单">☰</button>
          <span class="m-bar__title">{{ store.world?.name || '沙盘' }}</span>
        </div>
        <template v-if="store.worldId">
          <div v-if="focusedKey && focusedNode && !focusedNode.current" class="viewing-bar">
            <span>正在查看历史章节：<b>{{ focusedNode.title }}</b></span>
            <n-button size="tiny" type="primary" @click="backToCurrent">回到当前章</n-button>
          </div>
          <div v-if="store.beat && store.beat.script" class="script-banner">
            <div class="script-banner__h" @click="scriptCollapsed = !scriptCollapsed">
              <span>📜 本章剧本 · 叙事{{ store.beat.title ? '（' + store.beat.title + '）' : '' }}</span>
              <span class="script-banner__toggle">{{ scriptCollapsed ? '展开 ▾' : '收起 ▴' }}</span>
            </div>
            <div v-show="!scriptCollapsed" class="script-banner__body">{{ store.beat.script }}</div>
          </div>
          <n-scrollbar class="stage" ref="stageRef">
            <div v-for="s in visibleScenes" :key="s.id" :id="'sc-' + s.id" class="scene"
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
                <template v-for="(m, i) in s.messages" :key="i">
                  <div v-if="m.kind === 'do'" class="line__action">（{{ m.speaker_name }} {{ m.content }}）</div>
                  <div v-else-if="m.kind === 'think'" class="line__think">💭 {{ m.speaker_name }} · 心声：{{ m.content }}</div>
                  <div v-else-if="m.kind === 'narration'" class="line__narration">{{ m.content }}</div>
                  <div v-else class="line">
                    <span class="avatar avatar--sm" :style="{ background: nameColor(m.speaker_name) }">{{ first(m.speaker_name) }}</span>
                    <div class="line__body">
                      <div class="line__name">{{ m.speaker_name }}</div>
                      <div class="line__content">{{ m.content }}</div>
                    </div>
                  </div>
                </template>
                <div v-if="!s.messages.length" class="hint">（尚无对话，点「下一轮」开始）</div>
              </div>
            </div>
            <div v-if="!visibleScenes.length" class="empty">
              <n-icon size="44"><PlanetOutline /></n-icon>
              <div v-if="store.scenes.length">本章还没有场景。写下（可选）导演指示，点「下一轮」开始这一章。</div>
              <div v-else>还没有推演。写下（或留空）导演指示，点「下一轮」开始第一幕。</div>
            </div>
          </n-scrollbar>

          <div class="controls">
            <div v-if="store.chapterDone" class="chapter-done">
              <n-icon><CheckmarkCircleOutline /></n-icon>
              本章剧情已完成，点「进入下一章」继续推进
            </div>
            <n-input v-model:value="directive" type="textarea" :autosize="{ minRows: 1, maxRows: 4 }"
              placeholder="（可选）导演指示：想让剧情往哪走、引入什么……" />
            <div class="btns">
              <n-button type="primary" :loading="store.busy" :disabled="store.busy || store.chapterDone" @click="step">
                <template #icon><n-icon><PlayOutline /></n-icon></template>下一轮
              </n-button>
              <n-button type="info" :loading="store.busy" :disabled="store.busy || store.chapterDone" @click="nextScene">
                <template #icon><n-icon><AddOutline /></n-icon></template>新建场景
              </n-button>
              <n-button type="success" :loading="store.busy" :disabled="store.busy || store.chapterDone" @click="runScene">
                <template #icon><n-icon><PlayForwardOutline /></n-icon></template>自动演完本场景
              </n-button>
              <n-button type="warning" :loading="store.busy" :disabled="store.busy || store.chapterDone" @click="runChapter">
                <template #icon><n-icon><FlashOutline /></n-icon></template>自动演完本章
              </n-button>
              <n-button :type="store.chapterDone ? 'primary' : 'info'" :ghost="!store.chapterDone"
                :class="{ 'btn-pulse': store.chapterDone }"
                :loading="store.busy" :disabled="store.busy" @click="newChapter">
                <template #icon><n-icon><BookOutline /></n-icon></template>进入下一章
              </n-button>
              <n-button type="error" ghost :disabled="!store.canRollback || store.busy" @click="rollback">
                <template #icon><n-icon><ArrowUndoOutline /></n-icon></template>回退一步
              </n-button>
              <span class="btns__sep"></span>
              <n-button ghost :loading="genningScript" :disabled="store.busy" @click="genScript" title="叙事 agent 为当前章写剧本节奏，Keeper 据此推进">
                <template #icon><n-icon><SparklesOutline /></n-icon></template>叙事·写本章剧本
              </n-button>
              <n-button type="primary" ghost :disabled="store.busy" @click="openManuscript">
                <template #icon><n-icon><DocumentTextOutline /></n-icon></template>✍ 成稿
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

    <!-- 沙盘设置浮窗：参考文风 + 剧本大纲 -->
    <n-modal v-model:show="showSettings" preset="card" title="沙盘设置" class="settings-modal"
      :style="{ maxWidth: '680px', width: '92vw' }">
      <div class="settings">
        <!-- 参考文风 -->
        <div class="settings__sec">
          <div class="settings__h">参考文风</div>
          <n-input v-model:value="styleDraft" type="textarea"
            :autosize="{ minRows: 3, maxRows: 10 }"
            placeholder="粘贴一段想要的文风范例，或描述风格（如：冷峻克制、古龙式短句、大量留白……）" />
          <div class="settings__hint">文风会加入每次生成的上下文，指导角色发言与场景叙述的语言风格。</div>
          <div class="settings__actions">
            <n-button size="small" type="primary" :loading="savingStyle" @click="saveSettings">保存文风</n-button>
          </div>
        </div>

        <!-- 剧本大纲 -->
        <div class="settings__sec">
          <div class="settings__h">
            <span>剧本大纲</span>
            <div class="settings__h-btns">
              <n-button size="small" :loading="genningScript" :disabled="!store.outline.length" @click="genScript"
                title="叙事 agent 为「当前章」生成剧本节奏">叙事·写本章剧本</n-button>
              <n-button size="small" type="primary" :loading="genning" @click="genOutline">
                <template #icon><n-icon><component :is="store.outline.length ? RefreshOutline : SparklesOutline" /></n-icon></template>
                {{ store.outline.length ? '重写大纲' : '生成大纲' }}
              </n-button>
            </div>
          </div>
          <div v-if="genning" class="gen-stream">
            <div class="gen-stream__tip"><n-icon class="gen-stream__spin"><RefreshOutline /></n-icon> 正在生成大纲…</div>
            <pre v-if="genStreamText" class="gen-stream__text">{{ genStreamText }}</pre>
          </div>
          <div class="outline-list">
            <div v-for="(b, i) in editOutline" :key="i" class="ol">
              <div class="ol__row">
                <span class="ol__no" :class="{ 'ol__no--cur': i === store.beatIndex }">{{ i + 1 }}</span>
                <n-input v-model:value="b.title" size="small" placeholder="章节名" />
                <n-button size="tiny" text @click="removeBeat(i)">✕</n-button>
              </div>
              <n-input v-model:value="b.goal" size="small" type="textarea" :autosize="{ minRows: 1, maxRows: 3 }" placeholder="本章目标/大纲" />
              <n-input v-model:value="b.script" size="small" type="textarea" :autosize="{ minRows: 1, maxRows: 5 }"
                placeholder="本章剧本/节奏（叙事 agent 生成，Keeper 据此推进；可手改）" class="ol__script" />
            </div>
            <div v-if="!editOutline.length" class="settings__hint">点「生成大纲」让编剧写主线，或「+ 章」手动加</div>
          </div>
          <div class="settings__actions">
            <n-button size="small" @click="addBeat">+ 章</n-button>
            <n-button size="small" type="primary" @click="saveOutline">保存大纲</n-button>
          </div>
        </div>
      </div>
    </n-modal>

    <!-- 写作层：成稿浮窗 -->
    <n-modal v-model:show="showManuscript" preset="card" title="✍ 写作 · 成稿" class="ms-modal"
      :style="{ maxWidth: '880px', width: '94vw' }">
      <div class="ms">
        <div class="ms__pick">
          <div class="ms__pick-h">选择章节（基于已推演的场景）</div>
          <div class="ms__chips">
            <span v-for="ch in store.chapters" :key="ch.label"
              class="ms__chip" :class="{ 'ms__chip--on': selectedChapters.includes(ch.label) }"
              @click="toggleChapterSel(ch.label)">{{ ch.label }}（{{ ch.scenes.length }}场）</span>
            <span v-if="!store.chapters.length" class="settings__hint">还没有已推演的章节</span>
          </div>
          <div class="ms__actions">
            <n-button size="small" :loading="writing" :disabled="!selectedChapters.length" @click="doWrite(false)">写选中章</n-button>
            <n-button size="small" type="primary" :loading="writing" :disabled="!store.chapters.length" @click="doWrite(true)">写全部章</n-button>
            <span class="ms__note">写作层把台词/动作/心声/旁白织成散文，较慢请稍候</span>
          </div>
        </div>
        <div v-if="writing" class="ms__loading"><n-icon class="gen-stream__spin"><RefreshOutline /></n-icon> 正在成稿…</div>
        <div v-if="store.manuscript.length" class="ms__result">
          <div v-for="ch in store.manuscript" :key="ch.label" class="ms__ch">
            <div class="ms__ch-h">
              <span class="ms__ch-title">{{ ch.label }}</span>
              <n-button size="tiny" text @click="copyChapter(ch)">复制本章</n-button>
            </div>
            <div v-if="ch.summary" class="ms__summary">摘要：{{ ch.summary }}</div>
            <div class="ms__prose">{{ ch.prose }}</div>
          </div>
        </div>
      </div>
    </n-modal>

    <!-- onboarding：一句话生成世界 -->
    <n-modal v-model:show="showGen" preset="card" title="✨ 一句话生成世界"
      :style="{ maxWidth: '600px', width: '92vw' }">
      <div class="gen">
        <n-input v-model:value="genPrompt" type="textarea" :autosize="{ minRows: 3, maxRows: 8 }"
          placeholder="用一句话描述你想要的世界 / 故事，例如：一个赛博朋克城市里，记忆可被买卖的黑市侦探，追查自己被偷走的一段记忆" />
        <div class="gen__hint">系统会自动生成：世界观 / 角色 / 关系 / 地点 / 物品 / 粗粒度里程碑（几个时间锚点）。约需十几秒。</div>
        <div class="gen__actions">
          <n-button type="primary" :loading="genWorlding" :disabled="!genPrompt.trim()" @click="doGenWorld">
            生成世界
          </n-button>
        </div>
        <div v-if="genResult" class="gen__result">
          <div><b>{{ genResult.name }}</b> 已生成 ✓ — 已自动选中，可直接「下一轮」开始推演</div>
          <div class="gen__line">角色：{{ (genResult.characters || []).join('、') }}</div>
          <div class="gen__line">地点：{{ (genResult.locations || []).join('、') }}</div>
          <div class="gen__line">里程碑：{{ (genResult.milestones || []).join('  →  ') }}</div>
        </div>
      </div>
    </n-modal>

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
  NDrawer, NDrawerContent, NModal, useMessage,
} from 'naive-ui'
import {
  PlanetOutline, PlayOutline, PlayForwardOutline, FlashOutline,
  ArrowUndoOutline, BookOutline, AddOutline, RefreshOutline, SparklesOutline,
  CheckmarkCircleOutline, SettingsOutline, DocumentTextOutline,
} from '@vicons/ionicons5'
import { useStudioStore } from '@/store/Studio'
import AppNav from '@/components/AppNav.vue'

const store = useStudioStore()
const message = useMessage()
const directive = ref('')
const stageRef = ref(null)
const genning = ref(false)
const drawerOpen = ref(false)   // 手机端侧栏抽屉
const onSelectWorld = (id) => { store.select(id); drawerOpen.value = false }

const genStreamText = ref('')   // 流式生成大纲时的实时文本预览

// 沙盘设置：参考文风
const showSettings = ref(false)
const styleDraft = ref('')
const savingStyle = ref(false)
watch(() => store.styleGuide, (v) => { styleDraft.value = v || '' }, { immediate: true })
const saveSettings = async () => {
  savingStyle.value = true
  try { await store.saveSettings({ styleGuide: styleDraft.value }); message.success('设置已保存') }
  catch (e) { message.error('保存失败') }
  finally { savingStyle.value = false }
}
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
  genStreamText.value = ''
  showSettings.value = true   // 确保设置浮窗打开，让用户看到实时生成
  try {
    await store.generateOutlineStream(directive.value, (t) => { genStreamText.value += t })
    message.success('大纲已生成')
  } catch (e) {
    message.error(e?.message || '生成失败')
  } finally {
    genning.value = false
    genStreamText.value = ''
  }
}

// 叙事层：为「当前章」生成剧本节奏
const genningScript = ref(false)
const scriptCollapsed = ref(false)
const genScript = async () => {
  if (genningScript.value) return
  if (!store.outline.length) { message.warning('请先生成或添加大纲'); return }
  genningScript.value = true
  try {
    await store.generateScript(directive.value)
    message.success('本章剧本已生成')
  } catch (e) { message.error(e?.message || '生成失败') }
  finally { genningScript.value = false }
}

// 写作层：成稿
const showManuscript = ref(false)
const writing = ref(false)
const selectedChapters = ref([])
const openManuscript = async () => {
  showManuscript.value = true
  try { await store.loadManuscripts() } catch (e) { /* 忽略：没有成稿也正常 */ }
}
const toggleChapterSel = (label) => {
  const i = selectedChapters.value.indexOf(label)
  if (i >= 0) selectedChapters.value.splice(i, 1)
  else selectedChapters.value.push(label)
}
const doWrite = async (all) => {
  if (writing.value) return
  const labels = all ? [] : selectedChapters.value
  if (!all && !labels.length) { message.warning('请先选择章节'); return }
  writing.value = true
  try {
    await store.writeChapters(labels)
    message.success('成稿完成')
  } catch (e) { message.error(e?.message || '成稿失败') }
  finally { writing.value = false }
}
const copyChapter = async (ch) => {
  try { await navigator.clipboard.writeText(`【${ch.label}】\n\n${ch.prose}`); message.success('已复制') }
  catch (e) { message.error('复制失败') }
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

// 舞台只显示「聚焦的那一章」：默认跟随当前章，点右侧章节/场景可查看历史章。
const focusedKey = ref(null)   // null = 跟随当前章；否则为某章的 key（如「第2章」）
const focusedNode = computed(() => {
  const nodes = chapterNodes.value
  if (!nodes.length) return null
  if (focusedKey.value) {
    const n = nodes.find((x) => x.key === focusedKey.value)
    if (n) return n
  }
  return nodes.find((x) => x.current) || nodes[nodes.length - 1]
})
const visibleScenes = computed(() => focusedNode.value?.scenes || [])
// 推进剧情后回到当前章；切世界或换章也重置
const backToCurrent = () => { focusedKey.value = null }
watch(() => [store.worldId, store.beatIndex], backToCurrent)

const scrollBottom = () => nextTick(() => stageRef.value?.scrollTo({ position: 'bottom' }))
const focusChapter = (key) => {
  focusedKey.value = key
  drawerOpen.value = false
  nextTick(() => stageRef.value?.scrollTo({ position: 'top' }))
}
const focusScene = (id, key) => {
  if (key) focusedKey.value = key
  drawerOpen.value = false
  nextTick(() => {
    const el = document.getElementById('sc-' + id)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  })
}
watch(() => visibleScenes.value.map((s) => s.messages.length).join(','), scrollBottom)

const step = async () => {
  try {
    backToCurrent()
    const dir = directive.value
    directive.value = ''
    const timer = setInterval(scrollBottom, 300)
    try { await store.stepStream(dir) } finally { clearInterval(timer) }
    scrollBottom()
  } catch (e) { message.error('推演失败，请重试') }
}
const nextScene = async () => {
  try {
    backToCurrent()
    const r = await store.openScene(directive.value); directive.value = ''
    if (r?.data?.error) message.error(r.data.error)
    else if (r?.data?.name) message.success(`已开新场景：${r.data.name}`)
    scrollBottom()
  } catch (e) { message.error(e?.code === 'ECONNABORTED' ? '开场景超时，请重试' : '开场景失败') }
}
const runScene = async () => {
  try {
    backToCurrent()
    const dir = directive.value; directive.value = ''
    const timer = setInterval(scrollBottom, 300)
    try { await store.runSceneStream(dir) } finally { clearInterval(timer) }
    message.success('本场景已演完'); scrollBottom()
  } catch (e) { message.error(e?.message || '失败，请重试') }
}
const runChapter = async () => {
  try {
    backToCurrent()
    const dir = directive.value; directive.value = ''
    const timer = setInterval(scrollBottom, 300)
    try { await store.runChapterStream(dir) } finally { clearInterval(timer) }
    message.success('本章已演完'); scrollBottom()
  } catch (e) { message.error(e?.message || '失败，请重试') }
}
const newChapter = async () => {
  try {
    const r = await store.newChapter(directive.value); directive.value = ''
    if (r?.data?.chapter) message.success(`进入${r.data.chapter}`)
    scrollBottom()
  } catch (e) { message.error('进入下一章失败') }
}
const rollback = async () => {
  const r = await store.rollback()
  if (r?.data?.success) message.success('已回退一步')
  else message.error(r?.data?.error || '没有可回退的快照')
}

// onboarding：一句话生成世界
const showGen = ref(false)
const genPrompt = ref('')
const genWorlding = ref(false)
const genResult = ref(null)
const doGenWorld = async () => {
  if (genWorlding.value || !genPrompt.value.trim()) return
  genWorlding.value = true
  genResult.value = null
  try {
    const data = await store.generateWorld(genPrompt.value.trim())
    if (data?.error) { message.error(data.error); return }
    genResult.value = data
    message.success('世界已生成')
  } catch (e) { message.error(e?.message || '生成失败') }
  finally { genWorlding.value = false }
}

onMounted(() => store.fetchWorlds())
</script>

<style scoped>
.shell { display: flex; flex-direction: column; height: 100vh; height: 100dvh; }
.body { flex: 1; display: flex; min-height: 0; }

.sidebar { flex: 0 0 280px; background: var(--c-sidebar); color: var(--c-sidebar-text);
  padding: 14px 12px; display: flex; flex-direction: column; gap: 12px; min-height: 0; }
.sec { display: flex; flex-direction: column; gap: 8px; }
.sec--tree { flex: 1 1 auto; min-height: 0; }
.sec__head { display: flex; align-items: center; justify-content: space-between; font-weight: 600;
  font-size: 14px; cursor: pointer; }
.sec__title { font-weight: 600; font-size: 14px; }
.sec__body { display: flex; flex-direction: column; gap: 8px; }
.set__label { font-size: 12px; font-weight: 600; color: var(--c-sidebar-text); }
/* 深色侧栏里的「设置/大纲」按钮：用浅色文字，避免黑字看不清 */
.set-btn :deep(.n-button__content), .set-btn :deep(.n-icon) { color: var(--c-sidebar-text); }
.set-btn:hover :deep(.n-button__content), .set-btn:hover :deep(.n-icon) { color: #fff; }
/* 大纲编辑区有很多章时也能滚 */
.sec__body.outline-body { max-height: 240px; overflow-y: auto; }
.hint { color: #94a3b8; font-size: 12px; }
.gen-stream { background: var(--c-sidebar-soft); border-radius: 8px; padding: 8px; margin-bottom: 8px; }
.gen-stream__tip { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #6366f1; font-weight: 600; }
.gen-stream__spin { animation: gen-spin 1s linear infinite; }
.gen-stream__text { margin: 6px 0 0; max-height: 140px; overflow-y: auto; white-space: pre-wrap; word-break: break-word;
  font-size: 11px; line-height: 1.5; color: #475569; font-family: ui-monospace, Menlo, Consolas, monospace; }
@keyframes gen-spin { to { transform: rotate(360deg); } }

/* 设置浮窗 */
.settings { display: flex; flex-direction: column; gap: 22px; }
.settings__sec { display: flex; flex-direction: column; gap: 8px; }
.settings__h { display: flex; align-items: center; justify-content: space-between; gap: 10px;
  font-size: 15px; font-weight: 700; color: var(--c-text); }
.settings__hint { font-size: 12px; color: var(--c-text-faint); }
.settings__actions { display: flex; gap: 10px; }
.outline-list { display: flex; flex-direction: column; gap: 8px; max-height: 42vh; overflow-y: auto; padding-right: 2px; }

/* 大纲编辑 */
.ol { background: #f1f5f9; border-radius: 8px; padding: 7px 8px; display: flex; flex-direction: column; gap: 5px; }
.ol__row { display: flex; align-items: center; gap: 6px; }
.ol__no { width: 18px; height: 18px; border-radius: 50%; background: #e2e8f0; color: #475569;
  display: flex; align-items: center; justify-content: center; font-size: 11px; flex: 0 0 auto; }
.ol__no--cur { background: var(--c-primary); color: #fff; }
.ol__actions { display: flex; gap: 8px; }

/* 章节-场景树 */
.ch { margin-bottom: 2px; border-radius: 8px; }
.ch--cur { background: rgba(99,102,241,0.14); }
.ch__head { display: flex; align-items: center; gap: 6px; padding: 6px 6px;
  font-size: 13px; font-weight: 600; }
.ch__name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; cursor: pointer; }
.ch__name:hover { color: #e0e7ff; }
.ch--cur .ch__name { color: #c7d2fe; }
.ch__name--viewing { color: #fff; text-decoration: underline; }
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
.viewing-bar { display: flex; align-items: center; justify-content: space-between; gap: 12px;
  padding: 8px 28px; background: #fef3c7; color: #92400e; font-size: 13px; border-bottom: 1px solid #fde68a; }
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
.line__action { margin: 2px 0 2px 40px; font-style: italic; color: #64748b; font-size: 13px; line-height: 1.6; }
.line__think { margin: 2px 0 2px 40px; padding: 4px 10px; border-left: 2px dashed #cbd5e1;
  background: #f8fafc; color: #94a3b8; font-style: italic; font-size: 13px; line-height: 1.6;
  white-space: pre-wrap; word-break: break-word; }
.line__narration { margin: 10px auto; padding: 8px 16px; max-width: 90%; text-align: center;
  color: #b45309; background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px;
  font-size: 13.5px; line-height: 1.7; white-space: pre-wrap; word-break: break-word; }
.empty { height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 10px; color: #94a3b8; text-align: center; }

.controls { flex: 0 0 auto; padding: 14px 24px; background: var(--c-panel); border-top: 1px solid var(--c-border);
  display: flex; flex-direction: column; gap: 10px; }
.btns { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
.btns__sep { flex-basis: 100%; height: 0; }

/* 叙事层：本章剧本 banner */
.script-banner { margin: 0 24px 8px; border: 1px solid #fde68a; background: #fffbeb; border-radius: 8px;
  overflow: hidden; }
.script-banner__h { display: flex; justify-content: space-between; align-items: center; gap: 8px;
  padding: 6px 12px; font-size: 12.5px; font-weight: 600; color: #b45309; cursor: pointer; }
.script-banner__toggle { font-size: 11px; font-weight: 400; color: #d97706; }
.script-banner__body { padding: 2px 14px 10px; font-size: 13px; line-height: 1.7; color: #92400e;
  white-space: pre-wrap; word-break: break-word; }
.settings__h-btns { display: flex; gap: 8px; }
.ol__script { margin-top: 4px; }

/* 写作层：成稿浮窗 */
.ms { display: flex; flex-direction: column; gap: 14px; }
.ms__pick-h { font-size: 13px; font-weight: 600; color: #475569; margin-bottom: 8px; }
.ms__chips { display: flex; flex-wrap: wrap; gap: 8px; }
.ms__chip { font-size: 12.5px; padding: 4px 12px; border-radius: 999px; cursor: pointer;
  background: #f1f5f9; color: #475569; border: 1px solid #e2e8f0; user-select: none; }
.ms__chip--on { background: #6366f1; color: #fff; border-color: #6366f1; }
.ms__actions { display: flex; align-items: center; gap: 10px; margin-top: 12px; flex-wrap: wrap; }
.ms__note { font-size: 11.5px; color: #94a3b8; }
.ms__loading { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #6366f1; }
.ms__result { display: flex; flex-direction: column; gap: 18px; max-height: 60vh; overflow-y: auto; }
.ms__ch { border-top: 1px solid #e5e7eb; padding-top: 12px; }
.ms__ch-h { display: flex; justify-content: space-between; align-items: center; }
.ms__ch-title { font-size: 15px; font-weight: 700; color: #0f172a; }
.ms__summary { margin: 6px 0 10px; font-size: 12.5px; font-style: italic; color: #64748b;
  background: #f8fafc; border-left: 3px solid #cbd5e1; padding: 6px 10px; border-radius: 0 6px 6px 0; }
.ms__prose { font-size: 14px; line-height: 1.95; color: #1e293b; white-space: pre-wrap; word-break: break-word; }

.gen { display: flex; flex-direction: column; gap: 10px; }
.gen__hint { font-size: 12px; color: #94a3b8; line-height: 1.5; }
.gen__actions { display: flex; justify-content: flex-end; }
.gen__result { margin-top: 4px; padding: 10px 12px; background: #f0fdf4; border: 1px solid #dcfce7;
  border-radius: 8px; font-size: 13px; color: #166534; line-height: 1.7; }
.gen__line { color: #15803d; }
.chapter-done { display: flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 600;
  color: #15803d; background: #dcfce7; border: 1px solid #bbf7d0; border-radius: 8px; padding: 6px 10px; }
.btn-pulse { animation: btn-pulse 1.4s ease-in-out infinite; }
@keyframes btn-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(99,102,241,0.5); }
  50% { box-shadow: 0 0 0 6px rgba(99,102,241,0); }
}
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

/* 手机端顶栏（汉堡 + 标题），桌面隐藏 */
.m-bar { display: none; align-items: center; gap: 10px; padding: 8px 12px;
  background: var(--c-panel); border-bottom: 1px solid var(--c-border); flex: 0 0 auto; }
.m-bar__btn { border: none; background: var(--c-primary-soft); color: var(--c-primary);
  width: 34px; height: 34px; border-radius: 8px; font-size: 18px; cursor: pointer; flex: 0 0 auto; }
.m-bar__title { font-weight: 600; font-size: 15px; color: var(--c-text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.drawer-mask { display: none; position: fixed; inset: var(--nav-h) 0 0 0; background: rgba(15,23,42,0.45); z-index: 29; }

@media (max-width: 768px) {
  .sidebar {
    position: fixed; top: var(--nav-h); left: 0; bottom: 0; width: 84vw; max-width: 320px;
    transform: translateX(-100%); transition: transform 0.25s ease; z-index: 30;
    box-shadow: var(--shadow-md);
  }
  .sidebar--open { transform: translateX(0); }
  .drawer-mask { display: block; }
  .main { width: 100%; }
  .stage { padding: 14px 14px; }
  .controls { padding: 10px 14px; }
  .btns { gap: 8px; }
  .btns :deep(.n-button) { flex: 1 1 auto; }
  .viewing-bar { padding: 8px 14px; }
}
</style>
