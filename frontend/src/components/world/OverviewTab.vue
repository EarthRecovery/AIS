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
          <n-select v-model:value="wf.worldview_id" :options="worldviewOptions" clearable />
        </n-form-item>
        <n-button type="primary" @click="saveWorld">保存世界参数</n-button>
      </n-form>
    </n-card>

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
import { reactive, computed, watch } from 'vue'
import { NCard, NForm, NFormItem, NInput, NSelect, NButton } from 'naive-ui'
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
</style>
