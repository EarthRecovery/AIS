import { defineStore } from 'pinia'
import * as api from '@/api/sim'
import { listWorlds, updateWorld, generateWorld } from '@/api/world'

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
    styleGuide: '',       // 本沙盘的参考文风

    canRollback: false,
    busy: false,
    chapterDone: false,   // 裁判判定本章目标已达成（beat_done）→ 引导「进入下一章」
    // 角色详情面板
    charDetail: null,
    showChar: false,
    // 写作层：已成稿的章节 [{ label, summary, prose }]
    manuscript: [],
  }),
  actions: {
    async fetchWorlds() {
      this.worlds = (await listWorlds()).data?.worlds || []
    },
    // onboarding：一句话 → AI 生成世界，完成后自动选中
    async generateWorld(prompt) {
      const res = await generateWorld(prompt)
      const wid = res.data?.world_id
      await this.fetchWorlds()
      if (wid) await this.select(wid)
      return res.data
    },
    async select(worldId) {
      this.worldId = worldId
      this.chapterDone = false
      this.manuscript = []
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
      this.styleGuide = d.style_guide || ''
    },
    // 保存沙盘设置（目前含参考文风），写库后立即生效到后续生成 context
    async saveSettings({ styleGuide }) {
      if (!this.worldId) return
      await updateWorld(this.worldId, { style_guide: styleGuide ?? '' })
      this.styleGuide = styleGuide ?? ''
    },
    // 叙事层：为当前章生成剧本节奏(script)，写入 outline 后刷新
    async generateScript(directive) {
      if (!this.worldId) return null
      const res = await api.genScript(this.worldId, directive || '')
      await this.refresh()
      return res.data
    },
    // 写作层：把一或多章写成小说散文(labels 为空=全部)，写后自动落库
    async writeChapters(labels) {
      if (!this.worldId) return []
      const res = await api.writeChapters(this.worldId, labels && labels.length ? labels : null)
      this.manuscript = res.data?.chapters || []
      return this.manuscript
    },
    // 读取已落库的成稿
    async loadManuscripts() {
      if (!this.worldId) return
      const res = await api.listManuscripts(this.worldId)
      this.manuscript = res.data?.chapters || []
    },
    async generateOutline(directive) {
      if (!this.worldId) return null
      const res = await api.genOutline(this.worldId, directive || '')
      await this.refresh()
      return res.data
    },
    // 流式生成大纲：onToken 收到逐段文本用于实时预览，结束后刷新拿权威 outline
    async generateOutlineStream(directive, onToken) {
      if (!this.worldId) return null
      let beats = []
      await api.genOutlineStream(this.worldId, directive || '', (ev) => {
        if (ev.type === 'token') {
          if (onToken) onToken(ev.text)
        } else if (ev.type === 'done') {
          if (ev.outline) beats = ev.outline
        } else if (ev.type === 'error') {
          throw new Error(ev.message || '大纲生成失败')
        }
      })
      await this.refresh()
      return beats
    },
    async expandScene(sceneId) {
      const res = await api.simSceneMessages(sceneId)
      const s = this.scenes.find((x) => x.id === sceneId)
      if (s) { s.messages = res.data?.messages || []; s.collapsed = false }
    },
    async _run(fn) {
      if (this.busy || !this.worldId) return null
      this.busy = true
      this.chapterDone = false   // 任何推进/回退动作重新评估本章完成状态
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

    // 共用的流式事件处理：scene→插新场景块，speaker→新发言，token→逐字追加。
    // 适用于「下一轮 / 自动演完本场景 / 自动演完本章」（后两者可能含多个 scene 事件）。
    _simStreamHandler() {
      let activeScene = this.scenes.find((s) => s.id === this.activeSceneId)
      let curMsg = null
      return (ev) => {
        if (ev.type === 'scene') {
          // 新开的场景：先放一个空场景块，后续发言往里塞
          activeScene = {
            id: ev.scene_id, name: ev.name, scenario: ev.scenario,
            status: 'active', day_label: ev.day_label,
            participants: ev.participants || [], messages: [],
          }
          this.scenes.push(activeScene)
          this.activeSceneId = ev.scene_id
          curMsg = null
        } else if (ev.type === 'speaker') {
          if (!activeScene) activeScene = this.scenes.find((s) => s.id === this.activeSceneId)
          curMsg = { speaker_type: 'persona', speaker_name: ev.name, content: '', kind: 'say', _raw: '' }
          if (activeScene) activeScene.messages.push(curMsg)
        } else if (ev.type === 'token') {
          // 实时只显示 §动作§/§心理§ 标记之前的台词，避免标记露出来
          if (curMsg) { curMsg._raw += ev.text; curMsg.content = curMsg._raw.split('§')[0] }
        } else if (ev.type === 'speaker_done') {
          // 收尾：用解析好的台词，并把动作/心理作为独立的 kind 消息补到时间线
          if (curMsg) curMsg.content = (ev.say ?? curMsg.content) || ''
          const sc = activeScene || this.scenes.find((s) => s.id === this.activeSceneId)
          if (sc && ev.do) sc.messages.push({ speaker_type: 'persona', speaker_name: ev.name, content: ev.do, kind: 'do' })
          if (sc && ev.think) sc.messages.push({ speaker_type: 'persona', speaker_name: ev.name, content: ev.think, kind: 'think' })
        } else if (ev.type === 'narration') {
          // Keeper 旁白：推进剧情的关键事件
          const sc = activeScene || this.scenes.find((s) => s.id === this.activeSceneId)
          if (sc && ev.text) sc.messages.push({ speaker_type: 'narrator', speaker_name: '旁白', content: ev.text, kind: 'narration' })
        } else if (ev.type === 'judge') {
          // 裁判结算：本章目标达成则标记，引导用户「进入下一章」
          if (ev.chapter_done) this.chapterDone = true
        } else if (ev.type === 'error') {
          // 交给页面提示
          throw new Error(ev.message || '推演失败')
        }
      }
    },
    async _streamRun(streamFn, directive) {
      if (this.busy || !this.worldId) return
      this.busy = true
      this.chapterDone = false   // 本轮重新评估本章完成状态
      try {
        await streamFn(this.worldId, directive || '', this._simStreamHandler())
        // 结算后拉权威状态（stats/位置/记忆/可回退等）
        await this.refresh()
      } finally {
        this.busy = false
      }
    },
    // 流式跑一轮：发言逐 token 冒出
    stepStream(directive) { return this._streamRun(api.simStepStream, directive) },
    // 流式「自动演完本场景 / 本章」：逐幕逐轮 token 实时冒出
    runSceneStream(directive) { return this._streamRun(api.simRunSceneStream, directive) },
    runChapterStream(directive) { return this._streamRun(api.simRunChapterStream, directive) },
    newChapter(directive) { return this._run(() => api.simNewChapter(this.worldId, directive || '')) },
    runChapter(directive) { return this._run(() => api.simRunChapter(this.worldId, directive || '')) },
    runScene(directive) { return this._run(() => api.simRunScene(this.worldId, directive || '')) },
    rollback() { return this._run(() => api.simRollback(this.worldId)) },

    async openChar(charId) {
      if (!this.worldId) return
      const res = await api.charDetail(this.worldId, charId)
      this.charDetail = res.data || null
      this.showChar = true
    },
    async saveCharBasic(charId, payload) {
      await api.updateCharacter(charId, payload)
      await this.refresh()
    },
    async saveCharMental(charId, payload) {
      await api.upsertMental(charId, payload)
      const res = await api.charDetail(this.worldId, charId)
      this.charDetail = res.data || this.charDetail
    },
    async saveOutline(outline) {
      if (!this.worldId) return
      await api.updateOutline(this.worldId, outline)
      await this.refresh()
    },
  },
  getters: {
    // 章节 -> 该章节下的场景（左栏两层目录）
    chapters: (s) => {
      const map = new Map()
      for (const sc of s.scenes) {
        const key = sc.day_label || '未分章'
        if (!map.has(key)) map.set(key, [])
        map.get(key).push(sc)
      }
      return Array.from(map, ([label, scenes]) => ({ label, scenes }))
    },
  },
})
