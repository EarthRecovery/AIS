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
      this.canRollback = d.can_rollback
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
    runDay(directive) { return this._run(() => api.simRunDay(this.worldId, directive || '')) },
    rollback() { return this._run(() => api.simRollbackDay(this.worldId)) },
  },
})
