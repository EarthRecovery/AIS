import { defineStore } from 'pinia'
import {
  listWorldviews,
  createWorldview,
  listRooms,
  createRoom,
  getRoomDetail,
  deleteRoom,
  streamSay,
  streamAdvance,
} from '@/api/communication'

export const useCommunicationStore = defineStore('communication', {
  state: () => ({
    worldviews: [],
    rooms: [],
    // 当前房间
    roomId: null,
    roomName: '',
    scenario: '',
    worldview: null,
    participants: [], // [{ role_id, name }]
    messages: [],     // [{ speaker_type, speaker_role_id, speaker_name, content }]
    streaming: false,
  }),
  actions: {
    normalize(text) {
      let v = text != null ? String(text) : ''
      return v.replace(/\/n/g, '\n')
    },

    async fetchWorldviews() {
      const res = await listWorldviews()
      this.worldviews = res.data?.worldviews || []
    },
    async addWorldview(payload) {
      await createWorldview(payload)
      await this.fetchWorldviews()
    },

    async fetchRooms() {
      const res = await listRooms()
      this.rooms = res.data?.rooms || []
    },
    async addRoom(payload) {
      const res = await createRoom(payload)
      await this.fetchRooms()
      const newId = res.data?.id
      if (newId) await this.openRoom(newId)
      return newId
    },
    async removeRoom(roomId) {
      await deleteRoom(roomId)
      if (this.roomId === roomId) this.resetRoom()
      await this.fetchRooms()
    },

    resetRoom() {
      this.roomId = null
      this.roomName = ''
      this.scenario = ''
      this.worldview = null
      this.participants = []
      this.messages = []
    },

    async openRoom(roomId) {
      const res = await getRoomDetail(roomId)
      const data = res.data || {}
      if (data.error) return
      this.roomId = roomId
      this.roomName = data.room?.name || ''
      this.scenario = data.room?.scenario || ''
      this.worldview = data.worldview || null
      this.participants = data.participants || []
      this.messages = (data.messages || []).map((m) => ({ ...m }))
    },

    // speaker/token/done/error 事件驱动一个流式人格发言
    _consumeStream(streamFn) {
      let idx = -1
      return streamFn((ev) => {
        if (ev.type === 'speaker') {
          this.messages.push({
            speaker_type: 'persona',
            speaker_role_id: ev.role_id,
            speaker_name: ev.name,
            content: '',
          })
          idx = this.messages.length - 1
        } else if (ev.type === 'token') {
          if (idx >= 0) this.messages[idx].content += this.normalize(ev.text)
        } else if (ev.type === 'error') {
          this.messages.push({
            speaker_type: 'narrator',
            speaker_name: '系统',
            content: ev.message || '出错了',
          })
        }
      })
    },

    async sendMessage(content, targetRoleId = null) {
      if (!this.roomId || this.streaming) return
      const text = (content || '').trim()
      if (text) {
        this.messages.push({ speaker_type: 'user', speaker_name: '你', content: text })
      }
      this.streaming = true
      try {
        await this._consumeStream((onEvent) =>
          streamSay(this.roomId, text, targetRoleId, onEvent)
        )
      } catch (e) {
        console.error('say failed', e)
      } finally {
        this.streaming = false
      }
    },

    async advance(targetRoleId = null) {
      if (!this.roomId || this.streaming) return
      this.streaming = true
      try {
        await this._consumeStream((onEvent) =>
          streamAdvance(this.roomId, targetRoleId, onEvent)
        )
      } catch (e) {
        console.error('advance failed', e)
      } finally {
        this.streaming = false
      }
    },
  },
})
