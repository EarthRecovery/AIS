<template>
  <div class="tab">
    <n-card title="世界参数" size="small" class="card">
      <n-form label-placement="left" label-width="90">
        <n-form-item label="名称">
          <n-input v-model:value="wf.name" />
        </n-form-item>
        <n-form-item label="世界内时间">
          <n-input v-model:value="wf.in_world_time" placeholder="如：第3天 黄昏" />
        </n-form-item>
        <n-form-item label="状态">
          <n-select v-model:value="wf.status" :options="statusOptions" />
        </n-form-item>
        <n-form-item label="当前世界观">
          <div class="wv-row">
            <n-select v-model:value="wf.worldview_id" :options="worldviewOptions" clearable
              placeholder="选择一个世界观，或点右侧新建" />
            <n-button @click="showCreate = true">＋ 新建世界观</n-button>
          </div>
        </n-form-item>
        <n-button type="primary" @click="saveWorld">保存世界参数</n-button>
      </n-form>
    </n-card>

    <!-- 新建世界观（建好自动绑定为当前世界观） -->
    <n-modal v-model:show="showCreate" preset="card" title="新建世界观" style="max-width: 560px">
      <n-form label-placement="top">
        <n-form-item label="名称" required>
          <n-input v-model:value="cf.name" placeholder="例如：雾都侦探社 / 提瓦特大陆" />
        </n-form-item>
        <n-form-item label="公共设定（所有角色可知）">
          <n-input v-model:value="cf.description" type="textarea" :autosize="{ minRows: 2, maxRows: 8 }"
            placeholder="时代、地点、阵营、基调……会注入对话" />
        </n-form-item>
        <n-form-item label="世界规则（公共，可选）">
          <n-input v-model:value="cf.rules" type="textarea" :autosize="{ minRows: 1, maxRows: 6 }"
            placeholder="魔法体系、禁忌、物理法则等" />
        </n-form-item>
        <n-form-item>
          <template #label><span class="bg-label">完整背景设定 🔒 仅你可见</span></template>
          <n-input v-model:value="cf.background" type="textarea" :autosize="{ minRows: 3, maxRows: 12 }"
            placeholder="完整背景圣经：来龙去脉、隐藏真相……仅供整理思路，不发给角色。" />
        </n-form-item>
      </n-form>
      <template #footer>
        <div class="modal-footer">
          <n-button @click="showCreate = false">取消</n-button>
          <n-button type="primary" :disabled="!cf.name.trim()" :loading="creating" @click="submitCreate">
            创建并设为当前世界观
          </n-button>
        </div>
      </template>
    </n-modal>

    <n-card v-if="store.worldview" title="当前世界观（可更改）" size="small" class="card">
      <n-form label-placement="left" label-width="100">
        <n-form-item label="名称">
          <n-input v-model:value="vf.name" />
        </n-form-item>
        <n-form-item label="公共设定">
          <div class="field">
            <n-input v-model:value="vf.description" type="textarea" :autosize="{ minRows: 2, maxRows: 8 }"
              placeholder="所有角色都知道、会注入对话的世界概况" />
            <div class="layer-hint layer-hint--public">🌐 所有角色可知，会注入到对话</div>
          </div>
        </n-form-item>
        <n-form-item label="世界规则">
          <div class="field">
            <n-input v-model:value="vf.rules" type="textarea" :autosize="{ minRows: 2, maxRows: 6 }"
              placeholder="魔法体系、禁忌、物理法则等" />
            <div class="layer-hint layer-hint--public">🌐 公共可知</div>
          </div>
        </n-form-item>
        <n-form-item>
          <template #label><span class="bg-label">完整背景设定 🔒</span></template>
          <div class="field">
            <n-input v-model:value="vf.background" type="textarea" :autosize="{ minRows: 4, maxRows: 16 }"
              placeholder="完整世界观背景圣经：来龙去脉、隐藏真相、各方秘密……仅供你整理思路。" />
            <div class="layer-hint layer-hint--private">
              🔒 仅你可见，不会发给任何角色。角色只通过各自「认知/记忆」知道其中片段。
            </div>
          </div>
        </n-form-item>
        <n-button type="primary" @click="saveWorldview">保存世界观</n-button>
      </n-form>
    </n-card>
    <div v-else class="hint">该世界还没有绑定世界观，先在上方「当前世界观」里选择一个。</div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, watch } from 'vue'
import { NCard, NForm, NFormItem, NInput, NSelect, NButton, NModal } from 'naive-ui'
import { useWorldStore } from '@/store/World'
import { updateWorld, updateWorldview } from '@/api/world'

const store = useWorldStore()
const statusOptions = [
  { label: 'active 运行中', value: 'active' },
  { label: 'paused 暂停', value: 'paused' },
  { label: 'archived 归档', value: 'archived' },
]
const worldviewOptions = computed(() => store.worldviews.map((w) => ({ label: w.name, value: w.id })))

const wf = reactive({ name: '', in_world_time: '', status: 'active', worldview_id: null })
const vf = reactive({ name: '', description: '', rules: '', background: '' })

watch(
  () => store.world,
  (w) => { if (w) Object.assign(wf, { name: w.name, in_world_time: w.in_world_time, status: w.status, worldview_id: w.worldview_id }) },
  { immediate: true }
)
watch(
  () => store.worldview,
  (v) => { if (v) Object.assign(vf, { name: v.name, description: v.description || '', rules: v.rules || '', background: v.background || '' }) },
  { immediate: true }
)

const saveWorld = () => store.run(() => updateWorld(store.worldId, { ...wf }))
const saveWorldview = () =>
  store.run(() => updateWorldview(store.worldview.id, { ...vf, world_id: store.worldId }))

// 新建世界观 → 自动绑定为当前世界并刷新（下方编辑卡片随即出现）
const showCreate = ref(false)
const creating = ref(false)
const cf = reactive({ name: '', description: '', rules: '', background: '' })

const submitCreate = async () => {
  if (!cf.name.trim() || creating.value) return
  creating.value = true
  try {
    const id = await store.addWorldview({ ...cf })
    if (id) {
      wf.worldview_id = id
      await store.run(() => updateWorld(store.worldId, { worldview_id: id }))
    }
    cf.name = ''; cf.description = ''; cf.rules = ''; cf.background = ''
    showCreate.value = false
  } catch (e) {
    console.error('create worldview failed', e)
  } finally {
    creating.value = false
  }
}
</script>

<style scoped>
.tab { display: flex; flex-direction: column; gap: 16px; max-width: 760px; }
.card { background: #fff; }
.hint { color: #94a3b8; font-size: 13px; }
.field { width: 100%; }
.layer-hint { margin-top: 5px; font-size: 12px; line-height: 1.5; }
.layer-hint--public { color: #0891b2; }
.layer-hint--private { color: #7c3aed; }
.bg-label { color: #7c3aed; font-weight: 600; }
.wv-row { display: flex; gap: 10px; width: 100%; align-items: center; }
.wv-row :deep(.n-select) { flex: 1; }
.modal-footer { display: flex; justify-content: flex-end; gap: 12px; }
</style>
