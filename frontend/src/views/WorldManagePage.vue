<template>
  <div class="shell">
    <AppNav />
    <div class="body">
      <!-- 左侧：世界列表 -->
      <div class="sidebar">
        <div class="section__header">
          <span class="section__title"><n-icon><EarthOutline /></n-icon> 我的世界</span>
          <n-button size="tiny" type="primary" @click="showCreate = true">
            <template #icon><n-icon><AddOutline /></n-icon></template>新建
          </n-button>
        </div>
        <n-scrollbar style="flex: 1; min-height: 0">
          <div
            v-for="w in store.worlds"
            :key="w.id"
            class="world-item"
            :class="{ 'world-item--active': w.id === store.worldId }"
            @click="store.openWorld(w.id)"
          >
            <div class="world-item__main">
              <div class="world-item__name">{{ w.name }}</div>
              <div class="world-item__meta">
                <n-icon size="12"><TimeOutline /></n-icon>{{ w.in_world_time }}
              </div>
            </div>
            <span class="badge" :class="`badge--${w.status}`">{{ statusLabel(w.status) }}</span>
            <n-button text class="del" @click.stop="store.removeWorld(w.id)">
              <n-icon><TrashOutline /></n-icon>
            </n-button>
          </div>
          <div v-if="!store.worlds.length" class="empty-mini">
            <n-icon size="22"><EarthOutline /></n-icon>
            <span>还没有世界，点上方「新建」</span>
          </div>
        </n-scrollbar>
      </div>

      <!-- 右侧：参数编辑 -->
      <div class="main">
        <template v-if="store.worldId">
          <!-- 概览统计条：一眼看懂这个世界现在什么样 -->
          <div class="overview">
            <div class="overview__title">
              {{ store.world?.name }}
              <span class="overview__time"><n-icon><TimeOutline /></n-icon>{{ store.world?.in_world_time }}</span>
            </div>
            <div class="stats">
              <div v-for="s in stats" :key="s.label" class="stat">
                <n-icon size="18" :color="s.color"><component :is="s.icon" /></n-icon>
                <span class="stat__num">{{ s.value }}</span>
                <span class="stat__label">{{ s.label }}</span>
              </div>
            </div>
          </div>

          <n-tabs type="line" animated class="tabs" pane-style="padding-top: 8px">
            <n-tab-pane v-for="t in tabDefs" :key="t.name" :name="t.name">
              <template #tab>
                <span class="tab-label"><n-icon><component :is="t.icon" /></n-icon>{{ t.label }}</span>
              </template>
              <component :is="t.comp" />
            </n-tab-pane>
          </n-tabs>
        </template>
        <div v-else class="placeholder">
          <n-icon size="46" class="placeholder__icon"><EarthOutline /></n-icon>
          <div class="placeholder__title">从左侧选择或新建一个世界</div>
          <div class="placeholder__sub">在这里编辑角色、关系、物品、认知与世界观</div>
        </div>
      </div>
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
import { NButton, NScrollbar, NTabs, NTabPane, NModal, NForm, NFormItem, NInput, NSelect, NIcon } from 'naive-ui'
import {
  EarthOutline, AddOutline, TrashOutline, TimeOutline, PeopleOutline,
  LocationOutline, CubeOutline, GitNetworkOutline, AlbumsOutline, BookOutline,
  PlanetOutline,
} from '@vicons/ionicons5'
import { useWorldStore } from '@/store/World'
import AppNav from '@/components/AppNav.vue'
import OverviewTab from '@/components/world/OverviewTab.vue'
import CharactersTab from '@/components/world/CharactersTab.vue'
import LocationsTab from '@/components/world/LocationsTab.vue'
import ItemsTab from '@/components/world/ItemsTab.vue'
import RelationshipsTab from '@/components/world/RelationshipsTab.vue'
import TimelineTab from '@/components/world/TimelineTab.vue'
import SimulateTab from '@/components/world/SimulateTab.vue'

const store = useWorldStore()
const showCreate = ref(false)
const createForm = reactive({ name: '', worldview_id: null })
const worldviewOptions = computed(() => store.worldviews.map((w) => ({ label: w.name, value: w.id })))

const statusLabel = (s) => ({ active: '运行中', paused: '暂停', archived: '归档' }[s] || s)

const tabDefs = [
  { name: 'overview', label: '概览 / 世界观', icon: BookOutline, comp: OverviewTab },
  { name: 'simulate', label: '每日推演', icon: PlanetOutline, comp: SimulateTab },
  { name: 'characters', label: '角色', icon: PeopleOutline, comp: CharactersTab },
  { name: 'locations', label: '地点 / 住所', icon: LocationOutline, comp: LocationsTab },
  { name: 'items', label: '物品', icon: CubeOutline, comp: ItemsTab },
  { name: 'relationships', label: '关系', icon: GitNetworkOutline, comp: RelationshipsTab },
  { name: 'timeline', label: '事件时间线', icon: AlbumsOutline, comp: TimelineTab },
]

const stats = computed(() => [
  { label: '角色', value: store.characters.length, icon: PeopleOutline, color: '#2563eb' },
  { label: '地点', value: store.locations.length, icon: LocationOutline, color: '#059669' },
  { label: '物品', value: store.items.length, icon: CubeOutline, color: '#d97706' },
  { label: '关系', value: store.relationships.length, icon: GitNetworkOutline, color: '#db2777' },
  { label: '事件', value: store.events.length, icon: AlbumsOutline, color: '#7c3aed' },
])

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
.shell { display: flex; flex-direction: column; height: 100vh; }
.body { flex: 1; display: flex; min-height: 0; }

.sidebar {
  flex: 0 0 270px; background: var(--c-sidebar); color: var(--c-sidebar-text);
  padding: 18px 14px; display: flex; flex-direction: column; gap: 14px; min-height: 0;
}
.section__header { display: flex; justify-content: space-between; align-items: center; }
.section__title { display: flex; align-items: center; gap: 6px; font-weight: 600; font-size: 14px; }

.world-item {
  display: flex; align-items: center; gap: 8px;
  background: var(--c-sidebar-soft); border-radius: 10px; padding: 10px 12px;
  margin-bottom: 8px; cursor: pointer; transition: background 0.15s;
}
.world-item:hover { background: #3a4255; }
.world-item--active { background: var(--c-primary); color: #fff; }
.world-item__main { flex: 1; min-width: 0; }
.world-item__name { font-size: 14px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.world-item__meta { display: flex; align-items: center; gap: 4px; font-size: 12px; color: #9aa4b8; margin-top: 3px; }
.world-item--active .world-item__meta { color: #e0e7ff; }
.badge { font-size: 11px; padding: 2px 8px; border-radius: 999px; white-space: nowrap; }
.badge--active { background: #dcfce7; color: #15803d; }
.badge--paused { background: #fef9c3; color: #a16207; }
.badge--archived { background: #e2e8f0; color: #475569; }
.del { color: #94a3b8; }
.del:hover { color: #fca5a5; }
.empty-mini {
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  color: var(--c-text-faint); font-size: 12px; padding: 30px 10px;
}

.main { flex: 1 1 auto; min-width: 0; background: var(--c-bg); display: flex; flex-direction: column; }
.overview {
  flex: 0 0 auto; padding: 18px 28px 12px; background: var(--c-panel); border-bottom: 1px solid var(--c-border);
}
.overview__title { font-size: 20px; font-weight: 700; color: var(--c-text); display: flex; align-items: center; gap: 12px; }
.overview__time {
  display: inline-flex; align-items: center; gap: 4px; font-size: 12px; font-weight: 500;
  color: var(--c-primary); background: var(--c-primary-soft); padding: 3px 10px; border-radius: 999px;
}
.stats { display: flex; gap: 10px; margin-top: 14px; flex-wrap: wrap; }
.stat {
  display: flex; align-items: center; gap: 6px;
  background: #f8fafc; border: 1px solid var(--c-border); border-radius: 10px; padding: 8px 14px;
}
.stat__num { font-size: 18px; font-weight: 700; color: var(--c-text); }
.stat__label { font-size: 12px; color: var(--c-text-soft); }

/* n-tabs 自身做成纵向 flex：导航固定，分页内容区单独滚动 */
.tabs { flex: 1; min-height: 0; padding: 6px 28px 0; display: flex; flex-direction: column; overflow: hidden; }
.tabs :deep(.n-tabs-pane-wrapper) { flex: 1; min-height: 0; overflow-y: auto; }
.tabs :deep(.n-tab-pane) { padding-bottom: 28px; }
.tab-label { display: inline-flex; align-items: center; gap: 6px; }

.placeholder { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 6px; }
.placeholder__icon { color: #c7cdd9; }
.placeholder__title { color: var(--c-text-soft); font-size: 16px; font-weight: 600; }
.placeholder__sub { color: var(--c-text-faint); font-size: 13px; }
.footer { display: flex; justify-content: flex-end; gap: 12px; }
</style>
