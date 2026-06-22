<template>
  <n-modal
    :show="show"
    preset="card"
    title="新建房间"
    style="max-width: 560px"
    @update:show="(v) => emit('update:show', v)"
  >
    <n-form>
      <n-form-item label="房间名称">
        <n-input v-model:value="form.name" placeholder="例如：深夜酒馆的密谋" />
      </n-form-item>
      <n-form-item label="共享世界观">
        <n-select
          v-model:value="form.worldview_id"
          :options="worldviewOptions"
          placeholder="选择一个世界观（所有角色共享）"
        />
      </n-form-item>
      <n-form-item label="参与角色（至少 2 个）">
        <n-select
          v-model:value="form.role_ids"
          multiple
          :options="roleOptions"
          :loading="loadingRoles"
          placeholder="从已有人格中挑选"
        />
      </n-form-item>
      <n-form-item label="开场场景（可选）">
        <n-input
          v-model:value="form.scenario"
          type="textarea"
          :autosize="{ minRows: 2, maxRows: 5 }"
          placeholder="本场对话的具体情境，例如：暴雨夜，三人被困在山间小屋"
        />
      </n-form-item>
    </n-form>
    <template #footer>
      <div class="footer">
        <n-button @click="emit('update:show', false)">取消</n-button>
        <n-button type="primary" :disabled="!canSubmit" :loading="saving" @click="submit">
          创建房间
        </n-button>
      </div>
    </template>
  </n-modal>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { NModal, NForm, NFormItem, NInput, NSelect, NButton } from 'naive-ui'
import { useCommunicationStore } from '@/store/Communication'
import { getRoleList } from '@/api/role'

const props = defineProps({ show: { type: Boolean, default: false } })
const emit = defineEmits(['update:show'])

const store = useCommunicationStore()
const saving = ref(false)
const loadingRoles = ref(false)
const roleOptions = ref([])

const form = reactive({ name: '', worldview_id: null, role_ids: [], scenario: '' })

const worldviewOptions = computed(() =>
  store.worldviews.map((w) => ({ label: w.name, value: w.id }))
)

const canSubmit = computed(
  () => form.name.trim() && form.worldview_id && form.role_ids.length >= 2
)

const loadRoles = async () => {
  loadingRoles.value = true
  try {
    const res = await getRoleList()
    roleOptions.value = (res.data?.roles || []).map((r) => ({ label: r.name, value: r.id }))
  } catch (e) {
    console.error('load roles failed', e)
  } finally {
    loadingRoles.value = false
  }
}

watch(
  () => props.show,
  (v) => {
    if (v) {
      loadRoles()
      store.fetchWorldviews()
    }
  }
)

const submit = async () => {
  saving.value = true
  try {
    await store.addRoom({ ...form })
    form.name = ''
    form.worldview_id = null
    form.role_ids = []
    form.scenario = ''
    emit('update:show', false)
  } catch (e) {
    console.error('create room failed', e)
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.footer { display: flex; justify-content: flex-end; gap: 12px; }
</style>
