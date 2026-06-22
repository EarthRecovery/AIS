<template>
  <div class="tab">
    <div class="add">
      <n-input v-model:value="form.name" size="small" placeholder="地点名称" style="max-width: 200px" />
      <n-select v-model:value="form.type" size="small" :options="typeOptions" style="max-width: 160px" />
      <n-button size="small" type="primary" :disabled="!form.name.trim()" @click="add">+ 新建地点</n-button>
    </div>

    <div v-for="l in store.locations" :key="l.id" class="card">
      <div class="line">
        <n-input v-model:value="l.name" size="small" placeholder="名称" style="flex:2" />
        <n-select v-model:value="l.type" size="small" :options="typeOptions" style="flex:1" />
        <n-select v-model:value="l.parent_location_id" size="small" :options="parentOptions(l.id)" clearable placeholder="上级地点" style="flex:1" />
      </div>
      <n-input v-model:value="l.description" size="small" type="textarea" :autosize="{ minRows: 1, maxRows: 4 }" placeholder="描述" />
      <div class="row">
        <n-button size="tiny" type="primary" @click="save(l)">保存</n-button>
        <n-button size="tiny" @click="del(l.id)">删除</n-button>
      </div>
    </div>
    <div v-if="!store.locations.length" class="hint">还没有地点。住所请把类型设为 residence。</div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { NInput, NSelect, NButton } from 'naive-ui'
import { useWorldStore } from '@/store/World'
import { createLocation, updateLocation, deleteLocation } from '@/api/world'

const store = useWorldStore()
const typeOptions = [
  { label: 'residence 住所', value: 'residence' },
  { label: 'public 公共', value: 'public' },
  { label: 'landmark 地标', value: 'landmark' },
  { label: 'region 区域', value: 'region' },
]
const form = reactive({ name: '', type: 'public' })
const parentOptions = (selfId) =>
  store.locations.filter((l) => l.id !== selfId).map((l) => ({ label: l.name, value: l.id }))

const add = () => store.run(async () => { await createLocation(store.worldId, { ...form }); form.name = ''; form.type = 'public' })
const save = (l) => store.run(() => updateLocation(l.id, { name: l.name, type: l.type, description: l.description, parent_location_id: l.parent_location_id }))
const del = (id) => store.run(() => deleteLocation(id))
</script>

<style scoped>
.tab { display: flex; flex-direction: column; gap: 12px; max-width: 820px; }
.add { display: flex; gap: 10px; align-items: center; }
.card { background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; padding: 12px; display: flex; flex-direction: column; gap: 8px; }
.line { display: flex; gap: 8px; }
.row { display: flex; gap: 8px; }
.hint { color: #94a3b8; font-size: 13px; }
</style>
