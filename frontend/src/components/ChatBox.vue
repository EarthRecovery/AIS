<template>
  <div class="chatbox">
    <n-scrollbar
      class="chatbox__scroll"
      :style="{ height: '100%' }"
      :container-style="{ maxHeight: '100%' }"
      :content-style="{ paddingRight: '8px' }"
    >
      <div
        v-for="(message, index) in messages"
        :key="index"
        :class="['chat-message', `chat-message--${normalizeRole(message.role)}`]"
      >
        <n-card
          size="small"
          class="chat-bubble"
          :class="[`chat-bubble--${normalizeRole(message.role)}`]"
          embedded
        >
          <div class="chat-bubble__role">
            {{ roleLabel(message.role) }}
          </div>
          <div class="chat-bubble__content">
            {{ message.content }}
          </div>
        </n-card>
      </div>
      <div v-if="messages.length === 0" class="chatbox__empty">
        暂无对话，开始聊天吧～
      </div>
    </n-scrollbar>
  </div>
</template>

<script setup>
import { computed, onMounted, watch } from 'vue'
import { useChatHistoryStore } from '@/store/ChatHistory'
import { useTurnHistoryStore } from '@/store/TurnHistory'

const chatHistoryStore = useChatHistoryStore()
const turnHistoryStore = useTurnHistoryStore()

const messages = computed(() => chatHistoryStore.chatHistory)

const normalizeRole = (role) => {
  const lowered = String(role || '').toLowerCase()
  if (['assistant', 'ai', 'system'].includes(lowered)) {
    return 'assistant'
  }
  return 'user'
}

const roleLabel = (role) => (normalizeRole(role) === 'assistant' ? 'AI' : '我')

// 先确保 turn 历史加载，再同步首个 history 到 chat
onMounted(async () => {
  if (!turnHistoryStore.turn_history.length) {
    await turnHistoryStore.fetchTurnHistory()
  }
})

watch(
  () => turnHistoryStore.turn_history,
  async (list) => {
    if (list && list.length) {
      const first = list[0]
      const firstId = first?.id ?? first?.history_id ?? first?.turn_id
      if (firstId && chatHistoryStore.history_id !== firstId) {
        chatHistoryStore.history_id = firstId
        await chatHistoryStore.updateHistoryByHistoryId(firstId)
      }
    }
  },
  { immediate: true }
)
</script>

<style scoped>
.chatbox {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  width: 100%;
  height: 100%;
  padding: 20px 32px;
  background-color: #f8fafc;
  border-radius: 16px;
  border: 1px solid rgba(226, 232, 240, 0.9);
  box-sizing: border-box;
  overflow: hidden;
}

.chatbox__scroll {
  flex: 1;
  height: 100%;
}

.chatbox__empty {
  display: flex;
  height: 100%;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  font-size: 14px;
}

.chat-message {
  display: flex;
  margin-bottom: 12px;
}

.chat-message--user {
  justify-content: flex-end;
}

.chat-message--assistant {
  justify-content: flex-start;
}

.chat-bubble {
  max-width: 70%;
  border-radius: 18px;
  overflow: hidden;
}

.chat-bubble--user {
  background: linear-gradient(135deg, #e0f2fe, #bae6fd);
}

.chat-bubble--assistant {
  background: linear-gradient(135deg, #ede9fe, #ddd6fe);
}

.chat-bubble__role {
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 4px;
}

.chat-bubble__content {
  white-space: pre-wrap;
  word-break: break-word;
  color: #0f172a;
  line-height: 1.5;
}
</style>
