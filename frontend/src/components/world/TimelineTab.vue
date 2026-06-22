<template>
  <div class="tab">
    <div class="head">
      <span class="title">世界事件时间线（最新在上）</span>
      <n-button size="tiny" @click="store.refreshEvents()">刷新</n-button>
    </div>
    <div v-for="e in store.events" :key="e.id" class="event">
      <span class="kind" :style="{ background: kindColor(e.kind) }">{{ e.kind }}</span>
      <div class="body">
        <div class="summary">{{ e.summary || '(无摘要)' }}</div>
        <div v-if="e.payload && Object.keys(e.payload).length" class="payload">{{ fmt(e.payload) }}</div>
      </div>
      <span class="time">{{ e.in_world_time || '' }}</span>
    </div>
    <div v-if="!store.events.length" class="hint">还没有事件。对关系/物品/心智/认知/世界观/时间的更改会自动在这里留痕。</div>
  </div>
</template>

<script setup>
import { NButton } from 'naive-ui'
import { useWorldStore } from '@/store/World'

const store = useWorldStore()

const COLORS = {
  item_transfer: '#d97706', relationship_change: '#db2777', mental_update: '#7c3aed',
  belief_update: '#0891b2', worldview_change: '#dc2626', time_advance: '#2563eb',
  location_move: '#059669', ability_change: '#65a30d',
}
const kindColor = (k) => COLORS[k] || '#64748b'
const fmt = (p) => {
  try { return JSON.stringify(p) } catch (e) { return '' }
}
</script>

<style scoped>
.tab { display: flex; flex-direction: column; gap: 8px; max-width: 820px; }
.head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.title { font-weight: 600; color: #475569; }
.event { display: flex; gap: 12px; align-items: flex-start; background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; padding: 10px 12px; }
.kind { color: #fff; font-size: 11px; padding: 2px 8px; border-radius: 8px; white-space: nowrap; margin-top: 2px; }
.body { flex: 1; min-width: 0; }
.summary { color: #1e293b; font-size: 14px; }
.payload { color: #94a3b8; font-size: 12px; word-break: break-all; margin-top: 2px; }
.time { color: #64748b; font-size: 12px; white-space: nowrap; }
.hint { color: #94a3b8; font-size: 13px; }
</style>
