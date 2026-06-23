import { defineStore } from 'pinia'
import * as api from '@/api/sim'
import { listWorlds } from '@/api/world'

export const useStudioStore = defineStore('studio', {
  state: () => ({
    worlds: [],
    worldId: null,
    world: null,          // { id, name, in_world_time }
    scenes: [],           // [{ id, name, scenario, status, day_label, participants, messages }]
    characters: [],       // [{ id, name, status, location, stats }]
    activeSceneId: null,
    outline: [],
    beatIndex: 0,
    beat: null,
    canRollback: false,
    busy: false,
  }),
  actions: {
    async fetchWorlds() {
      this.worlds = (await listWorlds()).data?.worlds || []
    },
    async select(worldId) {
      this.worldId = worldId
      await this.refresh()
    },
    async refresh() {
      if (!this.worldId) return
      const d = (await api.simStatus(this.worldId)).data || {}
      if (d.error) return
      this.world = d.world
      this.scenes = d.scenes || []
      this.characters = d.characters || []
      this.activeSceneId = d.active_scene_id
      this.outline = d.outline || []
      this.beatIndex = d.beat_index || 0
      this.beat = d.beat || null
      this.canRollback = d.can_rollback
    },
    async generateOutline(directive) {
      if (!this.worldId) return null
      const res = await api.genOutline(this.worldId, directive || '')
      await this.refresh()
      return res.data
    },
    async expandScene(sceneId) {
      const res = await api.simSceneMessages(sceneId)
      const s = this.scenes.find((x) => x.id === sceneId)
      if (s) { s.messages = res.data?.messages || []; s.collapsed = false }
    },
    async _run(fn) {
      if (this.busy || !this.worldId) return null
      this.busy = true
      try {
        const res = await fn()
        await this.refresh()
        return res
      } finally {
        this.busy = false
      }
    },
    openScene(directive) { return this._run(() => api.simOpenScene(this.worldId, directive || '')) },
    step(directive) { return this._run(() => api.simStep(this.worldId, directive || '')) },

    // 流式跑一轮：发言逐 token 冒出
    async stepStream(directive) {
      if (this.busy || !this.worldId) return
      this.busy = true
      let activeScene = this.scenes.find((s) => s.id === this.activeSceneId)
      let curMsg = null
      try {
        await api.simStepStream(this.worldId, directive || '', (ev) => {
          if (ev.type === 'scene') {
            // 新开的场景：先放一个空场景块，后续发言往里塞
            activeScene = {
              id: ev.scene_id, name: ev.name, scenario: ev.scenario,
              status: 'active', day_label: ev.day_label,
              participants: ev.participants || [], messages: [],
            }
            this.scenes.push(activeScene)
            this.activeSceneId = ev.scene_id
          } else if (ev.type === 'speaker') {
            if (!activeScene) activeScene = this.scenes.find((s) => s.id === this.activeSceneId)
            curMsg = { speaker_type: 'persona', speaker_name: ev.name, content: '' }
            if (activeScene) activeScene.messages.push(curMsg)
          } else if (ev.type === 'token') {
            if (curMsg) curMsg.content += ev.text
          } else if (ev.type === 'error') {
            // 交给页面提示
            throw new Error(ev.message || '推演失败')
          }
        })
        // 结算后拉权威状态（stats/位置/记忆/可回退等）
        await this.refresh()
      } finally {
        this.busy = false
      }
    },
    runDay(directive) { return this._run(() => api.simRunDay(this.worldId, directive || '')) },
    rollback() { return this._run(() => api.simRollbackDay(this.worldId)) },
  },
})
