<template>
  <n-modal
    :show="visible"
    preset="card"
    title="设置"
    class="settings-modal"
    @close="handleClose"
    @mask-click="handleClose"
    :style="{ width: '520px', maxWidth: 'calc(100vw - 120px)' }"
  >
    <div class="settings">
      <div class="settings__row"> rag增强(只限制于moegirl, 输入一个名词让模型记住)</div>
      
      <div class="settings__row">
        
        <n-input v-model:value="inputValue" placeholder="请输入内容" />
        <n-button type="primary" @click="addContext" :loading="loading">提交</n-button>
      </div>
      <div class="settings__content">
        <slot>
          <p class="settings__placeholder">更多设置即将到来…</p>
        </slot>
      </div>
    </div>
  </n-modal>
</template>

<script setup>
import { ref, watch } from 'vue'
import { NModal, NInput, NButton, useMessage } from 'naive-ui'
import { ragAddContext, ragServiceAvailable } from '@/api/rag'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'submit'])
const inputValue = ref('')
const loading = ref(false)
const message = useMessage()

watch(
  () => props.visible,
  (val) => {
    if (!val) inputValue.value = ''
  }
)

const handleClose = () => {
  emit('close')
}

const addContext = async () => {
  if (!inputValue.value.trim() || loading.value) return
  loading.value = true
  try {
    const { data: status } = await ragServiceAvailable()
    if (!status?.available) {
      message.error('RAG 服务不可用，请稍后再试')
      return
    }
    await ragAddContext(inputValue.value.trim(), 'moegirl')
    message.success('已提交到 RAG')
    emit('submit', inputValue.value.trim())
    handleClose()
  } catch (error) {
    console.error('Failed to add context', error)
    message.error('提交失败，请稍后再试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.settings {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.settings__row {
  display: flex;
  gap: 12px;
  align-items: center;
}
.settings__row :deep(.n-input) {
  flex: 1;
}
.settings__content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.settings__placeholder {
  margin: 0;
  color: #64748b;
  font-size: 14px;
}
</style>
