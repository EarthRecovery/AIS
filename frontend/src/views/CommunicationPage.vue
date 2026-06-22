<template>
  <div class="page">
    <!-- 左侧：房间 / 世界观管理 -->
    <div class="sidebar">
      <div class="sidebar__top">
        <n-button text class="back" @click="goSingle">← 单人对话</n-button>
        <div class="title">多人剧场</div>
        <n-button size="tiny" @click="$router.push('/world')">⚙ 世界管理</n-button>
      </div>

      <div class="section">
        <div class="section__header">
          <span>世界观</span>
          <n-button size="tiny" @click="showWorldview = true">+ 新建</n-button>
        </div>
        <div class="chips">
          <span v-for="w in store.worldviews" :key="w.id" class="chip">{{ w.name }}</span>
          <span v-if="!store.worldviews.length" class="hint">先建一个共享世界观</span>
        </div>
      </div>

      <div class="section section--rooms">
        <div class="section__header">
          <span>房间</span>
          <n-button size="tiny" type="primary" @click="showRoom = true">+ 新建</n-button>
        </div>
        <n-scrollbar style="max-height: calc(100vh - 280px)">
          <div
            v-for="r in store.rooms"
            :key="r.id"
            class="room"
            :class="{ 'room--active': r.id === store.roomId }"
            @click="store.openRoom(r.id)"
          >
            <span class="room__name">{{ r.name }}</span>
            <n-button text class="room__del" @click.stop="store.removeRoom(r.id)">✕</n-button>
          </div>
          <div v-if="!store.rooms.length" class="hint">还没有房间</div>
        </n-scrollbar>
      </div>
    </div>

    <!-- 右侧：群聊 -->
    <div class="main">
      <template v-if="store.roomId">
        <div class="room-header">
          <div class="room-header__title">{{ store.roomName }}</div>
          <div class="room-header__meta">
            <span v-if="store.worldview" class="world">🌐 {{ store.worldview.name }}</span>
            <span
              v-for="p in store.participants"
              :key="p.role_id"
              class="part"
              :style="{ borderColor: color(p.role_id), color: color(p.role_id) }"
            >{{ p.name }}</span>
          </div>
          <div v-if="store.scenario" class="scenario">{{ store.scenario }}</div>
        </div>

        <GroupChatBox :messages="store.messages" :streaming="store.streaming" />

        <div class="input-bar">
          <n-select
            v-model:value="target"
            :options="targetOptions"
            size="small"
            class="target"
            placeholder="自动（导演选）"
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
            推进剧情
          </n-button>
          <n-button type="primary" :disabled="store.streaming" @click="send">发送</n-button>
        </div>
      </template>
      <div v-else class="placeholder">从左侧选择或新建一个房间开始多人对话</div>
    </div>

    <WorldviewModal v-model:show="showWorldview" />
    <RoomCreateModal v-model:show="showRoom" />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NInput, NSelect, NScrollbar } from 'naive-ui'
import { useCommunicationStore } from '@/store/Communication'
import GroupChatBox from '@/components/comm/GroupChatBox.vue'
import WorldviewModal from '@/components/comm/WorldviewModal.vue'
import RoomCreateModal from '@/components/comm/RoomCreateModal.vue'

const store = useCommunicationStore()
const router = useRouter()

const message = ref('')
const target = ref(null)
const showWorldview = ref(false)
const showRoom = ref(false)

const PALETTE = ['#2563eb', '#dc2626', '#059669', '#d97706', '#7c3aed', '#db2777', '#0891b2', '#65a30d']
const color = (roleId) => PALETTE[Math.abs(Number(roleId) || 0) % PALETTE.length]

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
const goSingle = () => router.push('/app')

onMounted(() => {
  store.fetchWorldviews()
  store.fetchRooms()
})
</script>

<style scoped>
.page { display: flex; width: 100%; height: 100vh; font-family: 'Poppins', sans-serif; }
.sidebar {
  flex: 0 0 22%; background-color: #414141; color: #cbd5e1;
  display: flex; flex-direction: column; padding: 20px 16px; gap: 18px;
}
.sidebar__top { display: flex; flex-direction: column; gap: 8px; }
.back { color: #93c5fd; align-self: flex-start; }
.title { font-size: 22px; font-weight: 700; color: #fff; }
.section__header {
  display: flex; justify-content: space-between; align-items: center;
  font-weight: 600; margin-bottom: 8px;
}
.chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chip {
  background: #4b5563; color: #e5e7eb; border-radius: 10px;
  padding: 3px 10px; font-size: 12px;
}
.hint { color: #94a3b8; font-size: 12px; }
.section--rooms { flex: 1 1 auto; min-height: 0; }
.room {
  display: flex; justify-content: space-between; align-items: center;
  background: #4b5563; border-radius: 10px; padding: 10px 12px;
  margin-bottom: 8px; cursor: pointer; transition: background 0.15s;
}
.room:hover { background: #5b6472; }
.room--active { background: #4f46e5; color: #fff; }
.room__name { font-size: 14px; }
.room__del { color: #cbd5e1; }

.main { flex: 1 1 auto; display: flex; flex-direction: column; background-color: #d5d5d5; min-width: 0; }
.room-header {
  flex: 0 0 auto; padding: 16px 28px; background: #fff; border-bottom: 1px solid #e5e7eb;
}
.room-header__title { font-size: 18px; font-weight: 700; color: #1e293b; }
.room-header__meta { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; align-items: center; }
.world { font-size: 12px; color: #475569; }
.part { font-size: 12px; border: 1px solid; border-radius: 10px; padding: 2px 8px; }
.scenario { margin-top: 8px; font-size: 13px; color: #64748b; }

.input-bar {
  flex: 0 0 auto; display: flex; gap: 10px; align-items: flex-end;
  padding: 14px 24px; background: linear-gradient(180deg, #f9fafb, #f1f3f5);
  border-top: 1px solid #e5e7eb;
}
.target { flex: 0 0 160px; }
.input-bar :deep(.n-input) { flex: 1; }
.placeholder {
  flex: 1; display: flex; align-items: center; justify-content: center;
  color: #6b7280; font-size: 15px;
}
</style>
