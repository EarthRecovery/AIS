<template>
  <div class="tab">
    <div class="add">
      <n-input v-model:value="form.name" size="small" placeholder="新角色名称" style="max-width: 200px" />
      <n-select
        v-model:value="form.role_id"
        size="small"
        :options="roleOptions"
        :loading="loadingRoles"
        clearable
        placeholder="基础人格（可选）"
        style="max-width: 220px"
      />
      <n-button size="small" type="primary" :disabled="!form.name.trim()" @click="add">+ 新建角色</n-button>
    </div>

    <n-collapse v-if="store.characters.length">
      <n-collapse-item
        v-for="b in store.characters"
        :key="b.character.id"
        :title="`${b.character.name}（${b.character.status}）`"
        :name="b.character.id"
      >
        <CharacterCard :block="b" />
      </n-collapse-item>
    </n-collapse>
    <div v-else class="hint">还没有角色，先新建一个。</div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { NCollapse, NCollapseItem, NInput, NSelect, NButton } from 'naive-ui'
import { useWorldStore } from '@/store/World'
import { createCharacter } from '@/api/world'
import { getRoleList } from '@/api/role'
import CharacterCard from './CharacterCard.vue'

const store = useWorldStore()
const form = reactive({ name: '', role_id: null })
const roleOptions = ref([])
const loadingRoles = ref(false)

const loadRoles = async () => {
  loadingRoles.value = true
  try {
    const res = await getRoleList()
    roleOptions.value = (res.data?.roles || []).map((r) => ({ label: r.name, value: r.id }))
  } finally {
    loadingRoles.value = false
  }
}

const add = () =>
  store.run(async () => {
    await createCharacter(store.worldId, { ...form })
    form.name = ''
    form.role_id = null
  })

onMounted(loadRoles)
</script>

<style scoped>
.tab { display: flex; flex-direction: column; gap: 14px; }
.add { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.hint { color: #94a3b8; font-size: 13px; }
</style>
