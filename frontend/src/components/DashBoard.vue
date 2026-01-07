<template>
  <div class="page">
    <div class="upper">
      <div class="upper_actions">
        <n-button type="primary" @click="handleOpenSettings" class="upper_button">
          设置
        </n-button>
        <n-select
          v-model:value="selectedRoleId"
          :options="roleOptions"
          :loading="isLoadingRoles"
          placeholder="选择角色"
          class="upper_select"
        />
        <n-button type="primary" @click="handleStartNewChat" :loading="isStarting" class="upper_button">
          新建对话
        </n-button>
      </div>
    </div>
    <div class="history">
        <div class="history_header">历史记录</div>
        <n-scrollbar style="height: 100%;">
          <div v-if="histories.length" class="history_list">
            <div
              v-for="turn in histories"
              :key="turn.id"
              class="history_item"
              :class="{ 'history_item--active': turn.id === activeTurnId }"
              @click="handleSelectTurn(turn.id)"
              role="button"
              tabindex="0"
              @keydown.enter.prevent="handleSelectTurn(turn.id)"
              @keydown.space.prevent="handleSelectTurn(turn.id)"
            >
              <div class="history_item__meta">
                <span class="history_item__label">回合</span>
                <span class="history_item__id">#{{ turn.id }}</span>
              </div>
              <p class="history_item__summary">
                {{ turn.summary || '暂无摘要' }}
              </p>
              <div class="history_item__footer">
                <span class="history_item__role" title="角色">
                  {{ turn.role_name || '默认角色' }}
                </span>
              </div>
            </div>
          </div>
          <div v-else class="history_empty">
            暂无历史记录
          </div>
        </n-scrollbar>
    </div>
    <SettingsPanel
      :visible="showSettings"
      @close="handleCloseSettings"
      @submit="handleSubmitSettings"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { NScrollbar, NButton, NSelect } from 'naive-ui'
import { useTurnHistoryStore } from '@/store/TurnHistory'
import { useChatHistoryStore } from '@/store/ChatHistory'
import SettingsPanel from './SettingsPanel.vue'
import { getRoleList } from '@/api/role'

const turnHistoryStore = useTurnHistoryStore()
const chatHistoryStore = useChatHistoryStore()
const histories = computed(() => turnHistoryStore.turn_history)
const isStarting = ref(false)
const isSwitching = ref(false)
const showSettings = ref(false)
const activeTurnId = computed(() => chatHistoryStore.history_id)
const selectedRoleId = ref(null)
const roleOptions = ref([])
const isLoadingRoles = ref(false)

const loadHistory = async () => {
  try {
    await turnHistoryStore.fetchTurnHistory()
  } catch (error) {
    console.error('failed to load turn history', error)
  }
}

const loadRoles = async () => {
  isLoadingRoles.value = true
  try {
    const res = await getRoleList()
    const roles = res?.data?.roles || []
    roleOptions.value = roles.map((role) => ({
      label: role.name,
      value: role.id
    }))
    if (!selectedRoleId.value && roleOptions.value.length) {
      selectedRoleId.value = roleOptions.value[0].value
    }
  } catch (error) {
    console.error('failed to load roles', error)
  } finally {
    isLoadingRoles.value = false
  }
}

const handleStartNewChat = async () => {
  if (isStarting.value) return
  isStarting.value = true
  try {
    await turnHistoryStore.startNewTurn(selectedRoleId.value)
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

const handleOpenSettings = () => {
  showSettings.value = true
}

const handleCloseSettings = () => {
  showSettings.value = false
}

const handleSubmitSettings = (payload) => {
  console.log('settings submit', payload)
  showSettings.value = false
}

onMounted(() => {
  loadHistory()
  loadRoles()
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
  flex: 0 0 auto;
  padding: 24px;
}
.upper_actions {
  display: flex;
  width: 100%;
  gap: 16px;
  flex-wrap: wrap;
  justify-content: center;
}
.upper_select {
  flex: 1 1 180px;
  max-width: 260px;
}
.upper_button {
  flex: 1 1 180px;
  max-width: 240px;
  height: 44px;
  font-size: 16px;
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
.history_item__footer {
  margin-top: 10px;
  display: flex;
  justify-content: flex-end;
}
.history_item__role {
  font-size: 12px;
  color: #475569;
  background: #f1f5f9;
  border-radius: 10px;
  padding: 4px 10px;
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
