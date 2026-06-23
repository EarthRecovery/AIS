<template>
  <div class="shell">
    <AppNav />
    <div class="body">
      <!-- 左侧：场景 / 世界观 -->
      <div class="sidebar">
        <div class="section">
          <div class="section__header">
            <span class="section__title"><n-icon><BookOutline /></n-icon> 世界观</span>
            <n-button size="tiny" secondary @click="showWorldview = true">
              <template #icon><n-icon><AddOutline /></n-icon></template>新建
            </n-button>
          </div>
          <div class="chips">
            <span v-for="w in store.worldviews" :key="w.id" class="chip">{{ w.name }}</span>
            <span v-if="!store.worldviews.length" class="hint">先建一个共享世界观</span>
          </div>
        </div>

        <div class="section section--rooms">
          <div class="section__header">
            <span class="section__title"><n-icon><PeopleOutline /></n-icon> 场景</span>
            <n-button size="tiny" type="primary" @click="showRoom = true">
              <template #icon><n-icon><AddOutline /></n-icon></template>新建
            </n-button>
          </div>
          <n-scrollbar style="flex: 1; min-height: 0">
            <div
              v-for="r in store.rooms"
              :key="r.id"
              class="room"
              :class="{ 'room--active': r.id === store.roomId }"
              @click="store.openRoom(r.id)"
            >
              <n-icon class="room__icon"><ChatbubblesOutline /></n-icon>
              <span class="room__name">{{ r.name }}</span>
              <n-button text class="room__del" @click.stop="store.removeRoom(r.id)">
                <n-icon><TrashOutline /></n-icon>
              </n-button>
            </div>
            <div v-if="!store.rooms.length" class="empty-mini">
              <n-icon size="22"><ChatbubblesOutline /></n-icon>
              <span>还没有场景，点上方「新建」</span>
            </div>
          </n-scrollbar>
        </div>
      </div>

      <!-- 右侧：群聊 -->
      <div class="main">
        <template v-if="store.roomId">
          <div class="room-header">
            <div class="room-header__row">
              <div class="room-header__title">{{ store.roomName }}</div>
              <span v-if="store.worldview" class="world-tag">
                <n-icon><EarthOutline /></n-icon>{{ store.worldview.name }}
              </span>
            </div>
            <!-- 在场角色头像 -->
            <div class="roster">
              <div
                v-for="p in store.participants"
                :key="p.role_id"
                class="avatar"
                :style="{ background: color(p.role_id) }"
                :title="p.name"
              >{{ firstChar(p.name) }}</div>
              <span class="roster__hint">{{ store.participants.length }} 位角色在场</span>
            </div>
            <div v-if="store.scenario" class="scenario">
              <n-icon><MapOutline /></n-icon>{{ store.scenario }}
            </div>
          </div>

          <GroupChatBox :messages="store.messages" :streaming="store.streaming" />

          <div class="input-bar">
            <n-select
              v-model:value="target"
              :options="targetOptions"
              size="small"
              class="target"
              placeholder="🎬 自动（导演选）"
              clearable
            />
            <n-input
              v-model:value="message"
              type="textarea"
              :autosize="{ minRows: 1, maxRows: 6 }"
              placeholder="以你的身份说点什么（可留空，直接点推进）"
              @keydown="onKeydown"
            />
            <n-button :disabled="store.streaming" :loading="store.streaming" @click="advance">
              <template #icon><n-icon><PlayForwardOutline /></n-icon></template>推进
            </n-button>
            <n-button type="primary" :disabled="store.streaming" @click="send">
              <template #icon><n-icon><SendOutline /></n-icon></template>发送
            </n-button>
          </div>
        </template>
        <div v-else class="placeholder">
          <n-icon size="46" class="placeholder__icon"><PeopleOutline /></n-icon>
          <div class="placeholder__title">从左侧选择或新建一个场景</div>
          <div class="placeholder__sub">让多个角色在共享世界观下对话</div>
        </div>
      </div>
    </div>

    <WorldviewModal v-model:show="showWorldview" />
    <RoomCreateModal v-model:show="showRoom" />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { NButton, NInput, NSelect, NScrollbar, NIcon } from 'naive-ui'
import {
  BookOutline, PeopleOutline, AddOutline, TrashOutline, ChatbubblesOutline,
  EarthOutline, MapOutline, PlayForwardOutline, SendOutline,
} from '@vicons/ionicons5'
import { useCommunicationStore } from '@/store/Communication'
import AppNav from '@/components/AppNav.vue'
import GroupChatBox from '@/components/comm/GroupChatBox.vue'
import WorldviewModal from '@/components/comm/WorldviewModal.vue'
import RoomCreateModal from '@/components/comm/RoomCreateModal.vue'

const store = useCommunicationStore()

const message = ref('')
const target = ref(null)
const showWorldview = ref(false)
const showRoom = ref(false)

const PALETTE = ['#2563eb', '#dc2626', '#059669', '#d97706', '#7c3aed', '#db2777', '#0891b2', '#65a30d']
const color = (roleId) => PALETTE[Math.abs(Number(roleId) || 0) % PALETTE.length]
const firstChar = (name) => (name || '?').trim().charAt(0)

const targetOptions = computed(() =>
  store.participants.map((p) => ({ label: `指定 ${p.name}`, value: p.role_id }))
)

const send = async () => {
  const content = message.value
  message.value = ''
  await store.sendMessage(content, target.value)
}
const advance = async () => {
  await store.advance(target.value)
}
const onKeydown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
  }
}

onMounted(() => {
  store.fetchWorldviews()
  store.fetchRooms()
})
</script>

<style scoped>
.shell { display: flex; flex-direction: column; height: 100vh; }
.body { flex: 1; display: flex; min-height: 0; }

.sidebar {
  flex: 0 0 260px; background: var(--c-sidebar); color: var(--c-sidebar-text);
  display: flex; flex-direction: column; padding: 18px 14px; gap: 18px; min-height: 0;
}
.section { display: flex; flex-direction: column; gap: 10px; }
.section--rooms { flex: 1 1 auto; min-height: 0; }
.section__header { display: flex; justify-content: space-between; align-items: center; }
.section__title { display: flex; align-items: center; gap: 6px; font-weight: 600; font-size: 14px; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chip { background: var(--c-sidebar-soft); color: #e5e7eb; border-radius: 8px; padding: 4px 10px; font-size: 12px; }
.hint { color: var(--c-text-faint); font-size: 12px; }

.room {
  display: flex; align-items: center; gap: 8px;
  background: var(--c-sidebar-soft); border-radius: 10px; padding: 10px 12px;
  margin-bottom: 8px; cursor: pointer; transition: background 0.15s, transform 0.1s;
}
.room:hover { background: #3a4255; }
.room--active { background: var(--c-primary); color: #fff; }
.room__icon { opacity: 0.8; }
.room__name { flex: 1; font-size: 14px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.room__del { color: #94a3b8; }
.room__del:hover { color: #fca5a5; }
.empty-mini {
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  color: var(--c-text-faint); font-size: 12px; padding: 30px 10px;
}

.main { flex: 1 1 auto; display: flex; flex-direction: column; background: var(--c-bg); min-width: 0; }
.room-header { flex: 0 0 auto; padding: 16px 28px; background: var(--c-panel); border-bottom: 1px solid var(--c-border); }
.room-header__row { display: flex; align-items: center; gap: 12px; }
.room-header__title { font-size: 18px; font-weight: 700; color: var(--c-text); }
.world-tag {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 12px; color: var(--c-primary); background: var(--c-primary-soft);
  padding: 3px 10px; border-radius: 999px;
}
.roster { display: flex; align-items: center; gap: 6px; margin-top: 10px; }
.avatar {
  width: 28px; height: 28px; border-radius: 50%; color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 700; box-shadow: var(--shadow-sm);
}
.roster__hint { font-size: 12px; color: var(--c-text-faint); margin-left: 4px; }
.scenario {
  display: flex; align-items: center; gap: 6px; margin-top: 10px;
  font-size: 13px; color: var(--c-text-soft);
}

.input-bar {
  flex: 0 0 auto; display: flex; gap: 10px; align-items: flex-end;
  padding: 14px 24px; background: var(--c-panel); border-top: 1px solid var(--c-border);
}
.target { flex: 0 0 170px; }
.input-bar :deep(.n-input) { flex: 1; }

.placeholder {
  flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 6px;
}
.placeholder__icon { color: #c7cdd9; }
.placeholder__title { color: var(--c-text-soft); font-size: 16px; font-weight: 600; }
.placeholder__sub { color: var(--c-text-faint); font-size: 13px; }
</style>
