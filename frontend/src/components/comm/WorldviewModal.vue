<template>
  <n-modal
    :show="show"
    preset="card"
    title="新建世界观"
    style="max-width: 560px"
    @update:show="(v) => emit('update:show', v)"
  >
    <n-form>
      <n-form-item label="世界观名称">
        <n-input v-model:value="form.name" placeholder="例如：雾都侦探社 / 提瓦特大陆" />
      </n-form-item>
      <n-form-item label="世界背景">
        <n-input
          v-model:value="form.description"
          type="textarea"
          :autosize="{ minRows: 3, maxRows: 8 }"
          placeholder="时代、地点、阵营、基调……所有角色共享的设定"
        />
      </n-form-item>
      <n-form-item label="世界规则（可选）">
        <n-input
          v-model:value="form.rules"
          type="textarea"
          :autosize="{ minRows: 2, maxRows: 6 }"
          placeholder="魔法体系、禁忌、物理法则等约束"
        />
      </n-form-item>
    </n-form>
    <template #footer>
      <div class="footer">
        <n-button @click="emit('update:show', false)">取消</n-button>
        <n-button type="primary" :disabled="!form.name.trim()" :loading="saving" @click="submit">
          创建
        </n-button>
      </div>
    </template>
  </n-modal>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { NModal, NForm, NFormItem, NInput, NButton } from 'naive-ui'
import { useCommunicationStore } from '@/store/Communication'

defineProps({ show: { type: Boolean, default: false } })
const emit = defineEmits(['update:show'])

const store = useCommunicationStore()
const saving = ref(false)
const form = reactive({ name: '', description: '', rules: '' })

const submit = async () => {
  saving.value = true
  try {
    await store.addWorldview({ ...form })
    form.name = ''
    form.description = ''
    form.rules = ''
    emit('update:show', false)
  } catch (e) {
    console.error('create worldview failed', e)
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.footer { display: flex; justify-content: flex-end; gap: 12px; }
</style>
