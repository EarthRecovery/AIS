<template>
  <div class="page">
    <div class="chat_box">
        <chatbox />
    </div>
    <div class="input_box">
      <div class="input-wrapper">
        <n-input
          v-model:value="message"
          type="textarea"
          minlength="1"
          class="chat-input"
          placeholder=""
          autosize
          :bordered="false"
        />
        <n-button
          type="primary"
          class="send-button"
          size="large"
          circle
          :disabled="!canSend"
          @click="sendMessage"
        >
          <template #icon>
            <n-icon>
              <PaperPlaneOutline />
            </n-icon>
          </template>
        </n-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { PaperPlaneOutline } from '@vicons/ionicons5'
import Chatbox from './ChatBox.vue'
import { useChatHistoryStore } from '@/store/ChatHistory'

const chatHistoryStore = useChatHistoryStore()

const message = ref('')

const canSend = computed(() => message.value.trim().length > 0)

const sendMessage = () => {
  if (!canSend.value) return
  chatHistoryStore.sendMessage(message.value)
  message.value = ''
}
</script>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100vh;
}

.chat_box {
  flex: 0 0 90%;
  min-height: 0;
  background-color: #ffffff;
  display: flex;
}

.input_box {
  flex: 1;
  padding: 16px 24px;
  background: linear-gradient(180deg, #f9fafb, #f1f3f5);
  border-top: 1px solid #e5e7eb;
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  width: 100%;
  max-width: 900px;
  margin: 0 auto;
}

.chat-input {
  flex: 1;
  box-shadow: 0 6px 20px rgba(15, 23, 42, 0.08);
  border-radius: 20px;
  overflow: hidden;
}

.chat-input :deep(.n-input__textarea-el) {
  padding: 16px 20px;
  font-size: 16px;
  line-height: 1.5;
  background-color: #fff;
  border-radius: 20px;
  resize: none;
}

.send-button {
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6px 16px rgba(37, 99, 235, 0.35);
}
</style>
