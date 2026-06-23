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
      <n-form-item label="角色知识库（可选）">
        <div class="kb">
          <n-input
            v-model:value="form.knowledge"
            type="textarea"
            :autosize="{ minRows: 3, maxRows: 12 }"
            placeholder="直接粘贴/输入角色相关知识，创建后由后端自动分段并建立检索库；对话时角色会按需检索。也可导入 txt / md 文件。"
          />
          <div class="kb__bar">
            <n-upload
              :default-upload="false"
              accept=".txt,.md,.markdown"
              :show-file-list="false"
              @change="onFile"
            >
              <n-button size="small" tertiary>
                <template #icon><n-icon><DocumentTextOutline /></n-icon></template>
                导入 txt / md
              </n-button>
            </n-upload>
            <span v-if="form.knowledge" class="kb__count">{{ form.knowledge.length }} 字</span>
          </div>
        </div>
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
  NModal, NForm, NFormItem, NInput, NButton, NDynamicTags, NUpload, NIcon, useMessage,
} from 'naive-ui'
import { DocumentTextOutline } from '@vicons/ionicons5'
import { setRole, addRoleKnowledge } from '@/api/role'

defineProps({ show: { type: Boolean, default: false } })
// created 事件回传 { id, name }，方便父组件刷新列表并选中
const emit = defineEmits(['update:show', 'created'])

const message = useMessage()
const saving = ref(false)
const form = reactive({ name: '', description: '', personality: [], knowledge: '' })

const reset = () => {
  form.name = ''
  form.description = ''
  form.personality = []
  form.knowledge = ''
}

// 读取导入的 txt / md 文件，追加到知识库文本框
const onFile = ({ file }) => {
  const raw = file?.file
  if (!raw) return
  const reader = new FileReader()
  reader.onload = (e) => {
    const text = String(e.target?.result || '')
    form.knowledge = form.knowledge ? `${form.knowledge}\n\n${text}` : text
    message.success(`已导入 ${raw.name}`)
  }
  reader.onerror = () => message.error('文件读取失败')
  reader.readAsText(raw)
}

const submit = async () => {
  if (!form.name.trim() || saving.value) return
  saving.value = true
  try {
    const res = await setRole({
      name: form.name.trim(),
      description: form.description || null,
      personality: form.personality.length ? form.personality : null,
    })
    const id = res?.data?.role_id
    // 有知识内容则建立检索库（后端分段索引）
    if (id && form.knowledge.trim()) {
      try {
        const kb = await addRoleKnowledge(id, form.knowledge.trim())
        if (kb?.data?.success) {
          message.success(`角色已创建，知识库已建立（${kb.data.chunks} 段）`)
        } else {
          message.warning(`角色已创建，但知识库建立失败：${kb?.data?.error || '未知错误'}`)
        }
      } catch (e) {
        console.error('index knowledge failed', e)
        message.warning('角色已创建，但知识库建立失败')
      }
    } else {
      message.success('角色已创建')
    }
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
.kb { width: 100%; }
.kb__bar { display: flex; align-items: center; gap: 12px; margin-top: 8px; }
.kb__count { font-size: 12px; color: #94a3b8; }
</style>
