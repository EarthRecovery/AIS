<template>
  <div class="tab">
    <div class="add">
      <n-input v-model:value="form.name" size="small" placeholder="物品名称" style="max-width: 220px" />
      <n-button size="small" type="primary" :disabled="!form.name.trim()" @click="add">+ 新建物品</n-button>
    </div>

    <div v-for="i in store.items" :key="i.id" class="card">
      <div class="line">
        <n-input v-model:value="i.name" size="small" placeholder="名称" style="flex:2" />
        <n-select v-model:value="i.owner_character_id" size="small" :options="store.characterOptions" clearable placeholder="持有者" style="flex:1" />
        <n-select v-model:value="i.location_id" size="small" :options="store.locationOptions" clearable placeholder="所在地点" style="flex:1" />
      </div>
      <n-input v-model:value="i.description" size="small" type="textarea" :autosize="{ minRows: 1, maxRows: 3 }" placeholder="描述" />
      <div class="row">
        <n-button size="tiny" type="primary" @click="save(i)">保存</n-button>
        <n-button size="tiny" @click="del(i.id)">删除</n-button>
        <span class="hint">改持有者会自动记一条 item_transfer 事件</span>
      </div>
    </div>
    <div v-if="!store.items.length" class="hint">还没有物品。</div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { NInput, NSelect, NButton } from 'naive-ui'
import { useWorldStore } from '@/store/World'
import { createItem, updateItem, deleteItem } from '@/api/world'

const store = useWorldStore()
const form = reactive({ name: '' })

const add = () => store.run(async () => { await createItem(store.worldId, { ...form }); form.name = '' })
const save = (i) => store.run(() => updateItem(i.id, {
  name: i.name, description: i.description,
  owner_character_id: i.owner_character_id, location_id: i.location_id,
}))
const del = (id) => store.run(() => deleteItem(id))
</script>

<style scoped>
.tab { display: flex; flex-direction: column; gap: 12px; max-width: 820px; }
.add { display: flex; gap: 10px; align-items: center; }
.card { background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; padding: 12px; display: flex; flex-direction: column; gap: 8px; }
.line { display: flex; gap: 8px; }
.row { display: flex; gap: 8px; align-items: center; }
.hint { color: #94a3b8; font-size: 12px; }
</style>
