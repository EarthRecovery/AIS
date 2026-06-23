import { defineStore } from 'pinia'
import * as api from '@/api/world'

export const useWorldStore = defineStore('world', {
  state: () => ({
    worlds: [],
    worldviews: [],
    // 当前世界详情
    worldId: null,
    world: null,
    worldview: null,
    characters: [], // [{ character, mental, abilities, beliefs }]
    locations: [],
    items: [],
    relationships: [],
    events: [],
    canRollback: false,
    loading: false,
  }),
  getters: {
    // 给 select 用的角色/地点选项
    characterOptions: (s) =>
      s.characters.map((b) => ({ label: b.character.name, value: b.character.id })),
    locationOptions: (s) =>
      s.locations.map((l) => ({ label: l.name, value: l.id })),
  },
  actions: {
    async fetchWorlds() {
      this.worlds = (await api.listWorlds()).data?.worlds || []
    },
    async fetchWorldviews() {
      this.worldviews = (await api.listWorldviews()).data?.worldviews || []
    },
    async addWorldview(payload) {
      const res = await api.createWorldview(payload)
      await this.fetchWorldviews()
      return res.data?.id
    },
    async createWorld(payload) {
      const res = await api.createWorld(payload)
      await this.fetchWorlds()
      if (res.data?.id) await this.openWorld(res.data.id)
      return res.data?.id
    },
    async removeWorld(id) {
      await api.deleteWorld(id)
      if (this.worldId === id) this.reset()
      await this.fetchWorlds()
    },
    reset() {
      this.worldId = null
      this.world = null
      this.worldview = null
      this.characters = []
      this.locations = []
      this.items = []
      this.relationships = []
      this.events = []
    },
    async openWorld(id) {
      this.loading = true
      try {
        const d = (await api.getWorld(id)).data || {}
        if (d.error) return
        this.worldId = id
        this.world = d.world
        this.worldview = d.worldview
        this.characters = d.characters || []
        this.locations = d.locations || []
        this.items = d.items || []
        this.relationships = d.relationships || []
        await this.refreshEvents()
        await this.refreshCanRollback()
      } finally {
        this.loading = false
      }
    },
    async refresh() {
      if (this.worldId) await this.openWorld(this.worldId)
    },
    async refreshEvents() {
      if (this.worldId) this.events = (await api.getWorldEvents(this.worldId)).data?.events || []
    },
    async refreshCanRollback() {
      if (this.worldId) this.canRollback = (await api.canRollback(this.worldId)).data?.can_rollback || false
    },
    async advanceDay(directive) {
      if (!this.worldId) return null
      const res = await api.advanceDay(this.worldId, directive || '')
      await this.refresh()
      await this.refreshCanRollback()
      return res.data
    },
    async rollbackDay() {
      if (!this.worldId) return null
      const res = await api.rollbackDay(this.worldId)
      await this.refresh()
      await this.refreshCanRollback()
      return res.data
    },

    // 通用：执行某个 api 调用后刷新世界详情
    async run(fn) {
      await fn()
      await this.refresh()
    },
  },
})
