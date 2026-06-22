<template>
  <div class="page">
    <!-- 左侧：世界列表 -->
    <div class="sidebar">
      <div class="sidebar__top">
        <n-button text class="back" @click="$router.push('/communication')">← 多人剧场</n-button>
        <div class="title">世界管理</div>
      </div>
      <div class="section__header">
        <span>世界</span>
        <n-button size="tiny" type="primary" @click="showCreate = true">+ 新建</n-button>
      </div>
      <n-scrollbar style="max-height: calc(100vh - 150px)">
        <div
          v-for="w in store.worlds"
          :key="w.id"
          class="world-item"
          :class="{ 'world-item--active': w.id === store.worldId }"
          @click="store.openWorld(w.id)"
        >
          <div>
            <div class="world-item__name">{{ w.name }}</div>
            <div class="world-item__meta">{{ w.in_world_time }} · {{ w.status }}</div>
          </div>
          <n-button text class="del" @click.stop="store.removeWorld(w.id)">✕</n-button>
        </div>
        <div v-if="!store.worlds.length" class="hint">还没有世界，新建一个</div>
      </n-scrollbar>
    </div>

    <!-- 右侧：参数编辑 -->
    <div class="main">
      <template v-if="store.worldId">
        <div class="main__header">
          {{ store.world?.name }}
          <span class="main__sub">所有参数可在下方各分页修改</span>
        </div>
        <n-tabs type="line" animated class="tabs">
          <n-tab-pane name="overview" tab="概览 / 世界观"><OverviewTab /></n-tab-pane>
          <n-tab-pane name="characters" tab="角色 / 心智 / 能力 / 认知"><CharactersTab /></n-tab-pane>
          <n-tab-pane name="locations" tab="地点 / 住所"><LocationsTab /></n-tab-pane>
          <n-tab-pane name="items" tab="物品"><ItemsTab /></n-tab-pane>
          <n-tab-pane name="relationships" tab="关系"><RelationshipsTab /></n-tab-pane>
          <n-tab-pane name="timeline" tab="事件时间线"><TimelineTab /></n-tab-pane>
        </n-tabs>
      </template>
      <div v-else class="placeholder">从左侧选择或新建一个世界开始编辑</div>
    </div>

    <!-- 新建世界 -->
    <n-modal v-model:show="showCreate" preset="card" title="新建世界" style="max-width: 480px">
      <n-form>
        <n-form-item label="世界名称">
          <n-input v-model:value="createForm.name" placeholder="例如：雾都长期世界" />
        </n-form-item>
        <n-form-item label="初始世界观（可选）">
          <n-select v-model:value="createForm.worldview_id" :options="worldviewOptions" clearable placeholder="可稍后设置" />
        </n-form-item>
      </n-form>
      <template #footer>
        <div class="footer">
          <n-button @click="showCreate = false">取消</n-button>
          <n-button type="primary" :disabled="!createForm.name.trim()" @click="submitCreate">创建</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { NButton, NScrollbar, NTabs, NTabPane, NModal, NForm, NFormItem, NInput, NSelect } from 'naive-ui'
import { useWorldStore } from '@/store/World'
import OverviewTab from '@/components/world/OverviewTab.vue'
import CharactersTab from '@/components/world/CharactersTab.vue'
import LocationsTab from '@/components/world/LocationsTab.vue'
import ItemsTab from '@/components/world/ItemsTab.vue'
import RelationshipsTab from '@/components/world/RelationshipsTab.vue'
import TimelineTab from '@/components/world/TimelineTab.vue'

const store = useWorldStore()
const showCreate = ref(false)
const createForm = reactive({ name: '', worldview_id: null })
const worldviewOptions = computed(() => store.worldviews.map((w) => ({ label: w.name, value: w.id })))

const submitCreate = async () => {
  await store.createWorld({ ...createForm })
  createForm.name = ''
  createForm.worldview_id = null
  showCreate.value = false
}

onMounted(() => {
  store.fetchWorlds()
  store.fetchWorldviews()
})
</script>

<style scoped>
.page { display: flex; width: 100%; height: 100vh; font-family: 'Poppins', sans-serif; }
.sidebar { flex: 0 0 22%; background: #414141; color: #cbd5e1; padding: 20px 16px; display: flex; flex-direction: column; gap: 14px; }
.sidebar__top { display: flex; flex-direction: column; gap: 6px; }
.back { color: #93c5fd; align-self: flex-start; }
.title { font-size: 22px; font-weight: 700; color: #fff; }
.section__header { display: flex; justify-content: space-between; align-items: center; font-weight: 600; }
.world-item { display: flex; justify-content: space-between; align-items: center; background: #4b5563; border-radius: 10px; padding: 10px 12px; margin-bottom: 8px; cursor: pointer; }
.world-item:hover { background: #5b6472; }
.world-item--active { background: #4f46e5; color: #fff; }
.world-item__name { font-size: 14px; font-weight: 600; }
.world-item__meta { font-size: 12px; color: #cbd5e1; margin-top: 2px; }
.del { color: #cbd5e1; }
.hint { color: #94a3b8; font-size: 12px; }
.main { flex: 1 1 auto; min-width: 0; background: #f3f4f6; display: flex; flex-direction: column; }
.main__header { padding: 16px 28px 0; font-size: 20px; font-weight: 700; color: #1e293b; }
.main__sub { font-size: 12px; color: #94a3b8; margin-left: 10px; font-weight: 400; }
.tabs { flex: 1; min-height: 0; padding: 8px 28px 28px; overflow: auto; }
.placeholder { flex: 1; display: flex; align-items: center; justify-content: center; color: #6b7280; }
.footer { display: flex; justify-content: flex-end; gap: 12px; }
</style>
