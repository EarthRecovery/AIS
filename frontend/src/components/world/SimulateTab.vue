<template>
  <div class="tab">
    <n-card size="small" class="card">
      <div class="head">
        <div>
          <div class="title">每日推演 · 结算</div>
          <div class="sub">当前世界时间：<b>{{ store.world?.in_world_time }}</b></div>
        </div>
        <n-tag type="warning" size="small" round>全量自主</n-tag>
      </div>

      <n-input
        v-model:value="directive"
        type="textarea"
        :autosize="{ minRows: 2, maxRows: 6 }"
        placeholder="（可选）这一天的导演指示：给个剧情走向、引入事件或人物、你想强调什么……留空则由世界自行推进。"
      />

      <div class="actions">
        <n-button type="primary" size="large" :loading="running" @click="advance">
          <template #icon><n-icon><PlayForwardOutline /></n-icon></template>
          结算这一天
        </n-button>
        <n-button size="large" :disabled="!store.canRollback || running" :loading="rolling" @click="rollback">
          <template #icon><n-icon><ArrowUndoOutline /></n-icon></template>
          回退一天
        </n-button>
        <span class="hint">结算会自动推进剧情、记忆、关系、认知，必要时新增角色 / 补充世界观 / 切换场景。可回退一天。</span>
      </div>
    </n-card>

    <n-card v-if="last" size="small" class="card" :title="`结算结果 → ${last.next_time || ''}`">
      <div class="summary">{{ last.day_summary || '（本次无叙事摘要）' }}</div>
      <div class="chips">
        <span class="chip" v-for="c in appliedChips" :key="c">{{ c }}</span>
      </div>
      <div class="tip">详细变化见「事件时间线」分页，角色/关系/物品等可在各分页手动调整。</div>
    </n-card>

    <div v-else class="empty">还没有结算过。写下（或留空）导演指示，点「结算这一天」让世界往前走一天。</div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { NCard, NInput, NButton, NIcon, NTag, useMessage } from 'naive-ui'
import { PlayForwardOutline, ArrowUndoOutline } from '@vicons/ionicons5'
import { useWorldStore } from '@/store/World'

const store = useWorldStore()
const message = useMessage()
const directive = ref('')
const running = ref(false)
const rolling = ref(false)
const last = ref(null)

const appliedChips = computed(() => {
  const a = last.value?.applied || {}
  const out = []
  if (a.events) out.push(`事件 ${a.events}`)
  if (a.memories) out.push(`记忆 ${a.memories}`)
  if (a.relationship_changes) out.push(`关系变化 ${a.relationship_changes}`)
  if (a.new_characters) out.push(`新增角色 ${a.new_characters}`)
  if (a.common_knowledge) out.push(`新增常识 ${a.common_knowledge}`)
  if (a.background_appended) out.push('补充背景')
  if (a.scene_switched) out.push('切换场景')
  return out.length ? out : ['无明显状态变化']
})

const advance = async () => {
  if (running.value) return
  running.value = true
  try {
    const res = await store.advanceDay(directive.value)
    if (res?.success) {
      last.value = res
      directive.value = ''
      message.success('已结算一天')
    } else {
      message.error(res?.error || '结算失败')
    }
  } catch (e) {
    console.error('advance day failed', e)
    message.error('结算失败，请重试')
  } finally {
    running.value = false
  }
}

const rollback = async () => {
  if (rolling.value) return
  rolling.value = true
  try {
    const res = await store.rollbackDay()
    if (res?.success) {
      last.value = null
      message.success(`已回退到「${res.restored_to || '上一天'}」`)
    } else {
      message.error(res?.error || '没有可回退的快照')
    }
  } catch (e) {
    console.error('rollback failed', e)
    message.error('回退失败，请重试')
  } finally {
    rolling.value = false
  }
}
</script>

<style scoped>
.tab { display: flex; flex-direction: column; gap: 16px; max-width: 760px; }
.card { background: #fff; }
.head { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }
.title { font-size: 16px; font-weight: 700; color: #1e293b; }
.sub { font-size: 13px; color: #64748b; margin-top: 2px; }
.actions { display: flex; gap: 12px; align-items: center; margin-top: 14px; flex-wrap: wrap; }
.hint { font-size: 12px; color: #94a3b8; flex: 1 1 240px; }
.summary { white-space: pre-wrap; line-height: 1.7; color: #1e293b; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px; }
.chip { background: #eef2ff; color: #4f46e5; border-radius: 999px; padding: 3px 10px; font-size: 12px; }
.tip { margin-top: 10px; font-size: 12px; color: #94a3b8; }
.empty { color: #94a3b8; font-size: 13px; }
</style>
