<template>
  <div class="cc">
    <!-- 状态栏：由 Keeper 根据剧情推演注入的叙事状态（一个词/短语） -->
    <div class="statusbar">
      <span class="statusbar__label">状态</span>
      <span class="statusbar__pill" :class="{ 'statusbar__pill--on': !!basic.condition }">
        {{ basic.condition || '正常' }}
      </span>
    </div>

    <!-- 基本属性 -->
    <n-form label-placement="left" label-width="80" class="block">
      <div class="block__title">基本</div>
      <n-form-item label="名称"><n-input v-model:value="basic.name" /></n-form-item>
      <n-form-item label="状态">
        <n-select v-model:value="basic.status" :options="statusOptions" />
      </n-form-item>
      <n-form-item label="当前状态">
        <n-input v-model:value="basic.condition"
          placeholder="如 轻伤（手）；由 Keeper 推演注入，也可手动改" />
      </n-form-item>
      <n-form-item label="所在地点">
        <n-select v-model:value="basic.current_location_id" :options="store.locationOptions" clearable />
      </n-form-item>
      <div class="row">
        <n-button size="small" type="primary" @click="saveBasic">保存基本</n-button>
        <n-button size="small" @click="removeChar">删除角色</n-button>
      </div>
    </n-form>

    <!-- 心智模型 -->
    <n-form label-placement="left" label-width="80" class="block">
      <div class="block__title">心智模型</div>
      <n-form-item label="情绪"><n-input v-model:value="mental.mood" /></n-form-item>
      <n-form-item label="目标"><n-input v-model:value="mental.goals" type="textarea" :autosize="{ minRows: 1, maxRows: 4 }" /></n-form-item>
      <n-form-item label="动机"><n-input v-model:value="mental.motivation" type="textarea" :autosize="{ minRows: 1, maxRows: 4 }" /></n-form-item>
      <n-form-item label="自我摘要"><n-input v-model:value="mental.self_summary" type="textarea" :autosize="{ minRows: 1, maxRows: 4 }" /></n-form-item>
      <n-button size="small" type="primary" @click="saveMental">保存心智</n-button>
    </n-form>

    <!-- 能力 -->
    <div class="block">
      <div class="block__title">能力</div>
      <div v-for="a in block.abilities" :key="a.id" class="line">
        <n-input v-model:value="a.name" size="small" placeholder="名称" style="flex:2" />
        <n-input-number v-model:value="a.level" size="small" :min="1" style="flex:1" />
        <n-button size="tiny" @click="saveAbility(a)">存</n-button>
        <n-button size="tiny" @click="delAbility(a.id)">删</n-button>
      </div>
      <div class="line">
        <n-input v-model:value="newAbility.name" size="small" placeholder="新能力名称" style="flex:2" />
        <n-input-number v-model:value="newAbility.level" size="small" :min="1" style="flex:1" />
        <n-button size="tiny" type="primary" :disabled="!newAbility.name.trim()" @click="addAbility">+ 添加</n-button>
      </div>
    </div>

    <!-- 认知 / 信念 -->
    <div class="block">
      <div class="block__title">认知（主观，可与真相不符）</div>
      <div v-for="b in block.beliefs" :key="b.id" class="belief">
        <n-input v-model:value="b.content" size="small" placeholder="认知内容" style="flex:3" />
        <n-input-number v-model:value="b.confidence" size="small" :min="0" :max="100" style="flex:1" />
        <span class="t">属实</span>
        <n-switch v-model:value="b.is_true" size="small" />
        <n-button size="tiny" @click="saveBelief(b)">存</n-button>
        <n-button size="tiny" @click="delBelief(b.id)">删</n-button>
      </div>
      <div class="belief">
        <n-input v-model:value="newBelief.content" size="small" placeholder="新认知内容" style="flex:3" />
        <n-input-number v-model:value="newBelief.confidence" size="small" :min="0" :max="100" style="flex:1" />
        <n-button size="tiny" type="primary" :disabled="!newBelief.content.trim()" @click="addBelief">+ 添加</n-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, watch } from 'vue'
import { NForm, NFormItem, NInput, NInputNumber, NSelect, NSwitch, NButton } from 'naive-ui'
import { useWorldStore } from '@/store/World'
import * as api from '@/api/world'

const props = defineProps({ block: { type: Object, required: true } })
const store = useWorldStore()

const statusOptions = [
  { label: 'active 在场', value: 'active' },
  { label: 'away 离开', value: 'away' },
  { label: 'dead 死亡', value: 'dead' },
]

const basic = reactive({ name: '', status: 'active', condition: '', current_location_id: null })
const mental = reactive({ mood: '', goals: '', motivation: '', self_summary: '' })
const newAbility = reactive({ name: '', level: 1 })
const newBelief = reactive({ content: '', confidence: 50 })

watch(
  () => props.block,
  (b) => {
    Object.assign(basic, {
      name: b.character.name, status: b.character.status,
      condition: b.character.condition || '',
      current_location_id: b.character.current_location_id,
    })
    Object.assign(mental, {
      mood: b.mental?.mood || '', goals: b.mental?.goals || '',
      motivation: b.mental?.motivation || '', self_summary: b.mental?.self_summary || '',
    })
  },
  { immediate: true, deep: false }
)

const cid = () => props.block.character.id
const saveBasic = () => store.run(() => api.updateCharacter(cid(), { ...basic }))
const removeChar = () => store.run(() => api.deleteCharacter(cid()))
const saveMental = () => store.run(() => api.upsertMental(cid(), { ...mental }))

const saveAbility = (a) => store.run(() => api.updateAbility(a.id, { name: a.name, level: a.level }))
const delAbility = (id) => store.run(() => api.deleteAbility(id))
const addAbility = () =>
  store.run(async () => { await api.createAbility(cid(), { ...newAbility }); newAbility.name = ''; newAbility.level = 1 })

const saveBelief = (b) =>
  store.run(() => api.updateBelief(b.id, { content: b.content, confidence: b.confidence, is_true: b.is_true }))
const delBelief = (id) => store.run(() => api.deleteBelief(id))
const addBelief = () =>
  store.run(async () => {
    await api.createBelief(store.worldId, {
      holder_character_id: cid(), subject_type: 'fact',
      content: newBelief.content, confidence: newBelief.confidence,
    })
    newBelief.content = ''; newBelief.confidence = 50
  })
</script>

<style scoped>
.cc { display: flex; flex-direction: column; gap: 14px; }
.block { background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 10px; padding: 12px 14px; }
.block__title { font-weight: 600; font-size: 13px; color: #475569; margin-bottom: 8px; }
.row { display: flex; gap: 10px; }
.line, .belief { display: flex; gap: 8px; align-items: center; margin-bottom: 6px; }
.t { font-size: 12px; color: #64748b; }
.statusbar { display: flex; align-items: center; gap: 10px; padding: 8px 12px;
  background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 10px; }
.statusbar__label { font-size: 12px; color: #94a3b8; }
.statusbar__pill { font-size: 13px; font-weight: 600; padding: 2px 12px; border-radius: 999px;
  background: #eef2f7; color: #64748b; }
.statusbar__pill--on { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
</style>
