<template>
  <div class="chatbox">
    <n-scrollbar class="chatbox__scroll" :style="{ height: '100%' }" ref="scrollRef">
      <div
        v-for="(m, index) in messages"
        :key="index"
        :class="['row', `row--${kind(m)}`]"
      >
        <div v-if="kind(m) === 'narrator'" class="narrator">
          {{ m.content }}
        </div>
        <n-card v-else size="small" embedded class="bubble" :class="`bubble--${kind(m)}`"
          :style="kind(m) === 'persona' ? { borderLeft: `4px solid ${color(m.speaker_role_id)}` } : null">
          <div class="bubble__name" :style="{ color: kind(m) === 'persona' ? color(m.speaker_role_id) : '#475569' }">
            {{ m.speaker_name }}
          </div>
          <div class="bubble__content">{{ m.content }}<span v-if="streaming && index === messages.length - 1" class="caret">▋</span></div>
        </n-card>
      </div>
      <div v-if="messages.length === 0" class="empty">
        还没有人发言。说点什么，或点「推进剧情」让角色们自己开场～
      </div>
    </n-scrollbar>
  </div>
</template>

<script setup>
import { watch, ref, nextTick } from 'vue'
import { NScrollbar, NCard } from 'naive-ui'

const props = defineProps({
  messages: { type: Array, default: () => [] },
  streaming: { type: Boolean, default: false },
})

const scrollRef = ref(null)

const kind = (m) => {
  if (m.speaker_type === 'user') return 'user'
  if (m.speaker_type === 'narrator') return 'narrator'
  return 'persona'
}

const PALETTE = ['#2563eb', '#dc2626', '#059669', '#d97706', '#7c3aed', '#db2777', '#0891b2', '#65a30d']
const color = (roleId) => PALETTE[Math.abs(Number(roleId) || 0) % PALETTE.length]

const scrollToBottom = () => {
  nextTick(() => scrollRef.value?.scrollTo({ position: 'bottom' }))
}
watch(() => props.messages.length, scrollToBottom)
watch(() => props.messages.map((m) => m.content).join('|'), scrollToBottom)
</script>

<style scoped>
.chatbox {
  flex: 1;
  min-height: 0;
  height: 100%;
  padding: 20px 28px;
  background-color: #f8fafc;
  box-sizing: border-box;
  overflow: hidden;
}
.chatbox__scroll { height: 100%; }
.empty {
  display: flex; height: 100%; align-items: center; justify-content: center;
  color: #94a3b8; font-size: 14px; text-align: center;
}
.row { display: flex; margin-bottom: 12px; }
.row--user { justify-content: flex-end; }
.row--persona { justify-content: flex-start; }
.row--narrator { justify-content: center; }
.narrator {
  font-size: 13px; color: #64748b; background: #eef2f6;
  padding: 6px 14px; border-radius: 12px;
}
.bubble { max-width: 72%; border-radius: 16px; overflow: hidden; }
.bubble--user { background: linear-gradient(135deg, #e0f2fe, #bae6fd); }
.bubble--persona { background: #ffffff; }
.bubble__name { font-size: 12px; font-weight: 700; margin-bottom: 4px; }
.bubble__content {
  white-space: pre-wrap; word-break: break-word; color: #0f172a; line-height: 1.6;
}
.caret { animation: blink 1s steps(1) infinite; color: #94a3b8; }
@keyframes blink { 50% { opacity: 0; } }
</style>
