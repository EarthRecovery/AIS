<template>
  <div class="tab">
    <div class="add">
      <n-select v-model:value="form.from_character_id" size="small" :options="store.characterOptions" placeholder="从（主体）" style="flex:1; min-width: 120px" />
      <span class="arrow">→</span>
      <n-select v-model:value="form.to_character_id" size="small" :options="store.characterOptions" placeholder="到（对象）" style="flex:1; min-width: 120px" />
      <n-input v-model:value="form.relation_type" size="small" placeholder="类型" style="max-width: 120px" />
      <n-button size="small" type="primary" :disabled="!canAdd" @click="add">+ 新建关系</n-button>
    </div>

    <div v-for="r in store.relationships" :key="r.id" class="card">
      <div class="head">
        <strong>{{ nameOf(r.from_character_id) }}</strong>
        <span class="arrow">→</span>
        <strong>{{ nameOf(r.to_character_id) }}</strong>
        <n-input v-model:value="r.relation_type" size="small" placeholder="类型" style="max-width: 140px" />
      </div>
      <div class="affinity">
        <span class="t">好感度 {{ r.affinity }}</span>
        <n-slider v-model:value="r.affinity" :min="-100" :max="100" style="flex:1" />
      </div>
      <n-input v-model:value="r.notes" size="small" type="textarea" :autosize="{ minRows: 1, maxRows: 3 }" placeholder="备注" />
      <div class="row">
        <n-button size="tiny" type="primary" @click="save(r)">保存</n-button>
        <n-button size="tiny" @click="del(r.id)">删除</n-button>
        <span class="hint">改类型/好感度会自动记 relationship_change 事件</span>
      </div>
    </div>
    <div v-if="!store.relationships.length" class="hint">还没有关系。关系是有向的（A→B 与 B→A 各一条）。</div>
  </div>
</template>

<script setup>
import { computed, reactive } from 'vue'
import { NSelect, NInput, NSlider, NButton } from 'naive-ui'
import { useWorldStore } from '@/store/World'
import { createRelationship, updateRelationship, deleteRelationship } from '@/api/world'

const store = useWorldStore()
const form = reactive({ from_character_id: null, to_character_id: null, relation_type: 'stranger', affinity: 0 })
const canAdd = computed(() => form.from_character_id && form.to_character_id)

const nameOf = (id) => store.characters.find((b) => b.character.id === id)?.character.name || `#${id}`

const add = () => store.run(async () => {
  await createRelationship(store.worldId, { ...form })
  form.from_character_id = null; form.to_character_id = null; form.relation_type = 'stranger'; form.affinity = 0
})
const save = (r) => store.run(() => updateRelationship(r.id, { relation_type: r.relation_type, affinity: r.affinity, notes: r.notes }))
const del = (id) => store.run(() => deleteRelationship(id))
</script>

<style scoped>
.tab { display: flex; flex-direction: column; gap: 12px; max-width: 820px; }
.add { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.arrow { color: #6366f1; font-weight: 700; }
.card { background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; padding: 12px; display: flex; flex-direction: column; gap: 8px; }
.head { display: flex; gap: 10px; align-items: center; }
.affinity { display: flex; gap: 12px; align-items: center; }
.t { font-size: 12px; color: #475569; white-space: nowrap; }
.row { display: flex; gap: 8px; align-items: center; }
.hint { color: #94a3b8; font-size: 12px; }
</style>
