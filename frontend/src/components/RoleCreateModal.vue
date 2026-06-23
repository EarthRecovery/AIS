<template>
  <n-modal
    :show="show"
    preset="card"
    title="新建角色"
    style="max-width: 560px"
    @update:show="(v) => emit('update:show', v)"
  >
    <n-form label-placement="top">
      <n-form-item label="角色名称" required>
        <n-input v-model:value="form.name" placeholder="例如：艾琳·诺斯" />
      </n-form-item>
      <n-form-item label="角色设定">
        <n-input
          v-model:value="form.description"
          type="textarea"
          :autosize="{ minRows: 3, maxRows: 8 }"
          placeholder="这个角色是谁、背景、说话方式、行为习惯……"
        />
      </n-form-item>
      <n-form-item label="性格特征">
        <n-dynamic-tags v-model:value="form.personality" />
      </n-form-item>
      <n-form-item label="默认场景（可选）">
        <n-input
          v-model:value="form.scenario"
          type="textarea"
          :autosize="{ minRows: 1, maxRows: 4 }"
          placeholder="角色登场的典型情境"
        />
      </n-form-item>
      <n-form-item label="RAG 知识名（可选）">
        <n-input v-model:value="form.rag_name" placeholder="如：moegirl 上的词条名，让角色掌握相关知识" />
      </n-form-item>
    </n-form>
    <template #footer>
      <div class="footer">
        <n-button @click="emit('update:show', false)">取消</n-button>
        <n-button type="primary" :disabled="!form.name.trim()" :loading="saving" @click="submit">
          创建角色
        </n-button>
      </div>
    </template>
  </n-modal>
</template>

<script setup>
import { reactive, ref } from 'vue'
import {
  NModal, NForm, NFormItem, NInput, NButton, NDynamicTags, useMessage,
} from 'naive-ui'
import { setRole } from '@/api/role'

defineProps({ show: { type: Boolean, default: false } })
// created 事件回传 { id, name }，方便父组件刷新列表并选中
const emit = defineEmits(['update:show', 'created'])

const message = useMessage()
const saving = ref(false)
const form = reactive({ name: '', description: '', personality: [], scenario: '', rag_name: '' })

const reset = () => {
  form.name = ''
  form.description = ''
  form.personality = []
  form.scenario = ''
  form.rag_name = ''
}

const submit = async () => {
  if (!form.name.trim() || saving.value) return
  saving.value = true
  try {
    const res = await setRole({
      name: form.name.trim(),
      description: form.description || null,
      personality: form.personality.length ? form.personality : null,
      scenario: form.scenario || null,
      rag_name: form.rag_name || null,
    })
    const id = res?.data?.role_id
    message.success('角色已创建')
    emit('created', { id, name: form.name.trim() })
    reset()
    emit('update:show', false)
  } catch (e) {
    console.error('create role failed', e)
    message.error('创建失败，请重试')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.footer { display: flex; justify-content: flex-end; gap: 12px; }
</style>
