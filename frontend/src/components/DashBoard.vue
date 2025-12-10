<template>
  <div class="page">
    <div class="upper">
        <n-button type="primary" @click="handleStartNewChat" :loading="isStarting" class="new_chat_button">
          新建对话
        </n-button>
    </div>
    <div class="history">
        <div class="history_header">历史记录</div>
        <n-scrollbar style="height: 100%;">
          <div v-if="histories.length" class="history_list">
            <div
              v-for="turn in histories"
              :key="turn.turn_id"
              class="history_item"
              :class="{ 'history_item--active': turn.turn_id === activeTurnId }"
              @click="handleSelectTurn(turn.turn_id)"
              role="button"
              tabindex="0"
              @keydown.enter.prevent="handleSelectTurn(turn.turn_id)"
              @keydown.space.prevent="handleSelectTurn(turn.turn_id)"
            >
              <div class="history_item__meta">
                <span class="history_item__label">回合</span>
                <span class="history_item__id">#{{ turn.turn_id }}</span>
              </div>
              <p class="history_item__summary">
                {{ turn.summary || '暂无摘要' }}
              </p>
            </div>
          </div>
          <div v-else class="history_empty">
            暂无历史记录
          </div>
        </n-scrollbar>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { NScrollbar, NButton } from 'naive-ui'
import { useTurnHistoryStore } from '@/store/TurnHistory'
import { useChatHistoryStore } from '@/store/ChatHistory'

const turnHistoryStore = useTurnHistoryStore()
const chatHistoryStore = useChatHistoryStore()
const histories = computed(() => turnHistoryStore.turn_history)
const isStarting = ref(false)
const isSwitching = ref(false)
const activeTurnId = computed(() => chatHistoryStore.turn_id)

const loadHistory = async () => {
  try {
    await turnHistoryStore.fetchTurnHistory()
  } catch (error) {
    console.error('failed to load turn history', error)
  }
}

const handleStartNewChat = async () => {
  if (isStarting.value) return
  isStarting.value = true
  try {
    await turnHistoryStore.startNewTurn()
  } catch (error) {
    console.error('failed to start new chat', error)
  } finally {
    isStarting.value = false
  }
}

const handleSelectTurn = async (turnId) => {
  if (isSwitching.value || turnId === activeTurnId.value) return
  isSwitching.value = true
  try {
    await turnHistoryStore.changeToTurn(turnId)
  } catch (error) {
    console.error(`failed to switch to turn ${turnId}`, error)
  } finally {
    isSwitching.value = false
  }
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100vh;
}
.upper {
  flex: 0 0 30%;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: 0 24px;
}
.history {
  flex: 0 0 70%;
  overflow: hidden;
  background-color: #414141;
  border-top: 1px solid #414141;
}
.history_header {
  height: 40px;
  line-height: 40px;
  text-align: center;
  font-weight: bold;
  font-size: 20px;
  /* border-bottom: 1px solid #ccc; */
}
.history_list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
}
.history_item {
  background-color: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 12px 16px;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
  cursor: pointer;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.1s ease;
}
.history_item:focus {
  outline: none;
  box-shadow: 0 0 0 2px #6366f1;
}
.history_item:hover {
  border-color: #6366f1;
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.2);
}
.history_item--active {
  border-color: #4f46e5;
  background: linear-gradient(135deg, #eef2ff, #e0e7ff);
}
.history_item__meta {
  display: flex;
  align-items: baseline;
  gap: 4px;
  font-size: 13px;
  color: #94a3b8;
}
.history_item__id {
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
}
.history_item__summary {
  margin: 8px 0 0;
  color: #1e293b;
  line-height: 1.6;
  font-size: 14px;
}
.history_empty {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  font-size: 14px;
}
.new_chat_button {
  margin-bottom: 8px;
  width: 80%;
  box-shadow: 0 6px 16px rgba(67, 252, 255, 0.35);
  margin-bottom: 20px;
}
</style>
