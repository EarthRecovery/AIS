import { defineStore } from 'pinia'
import { getTurnHistory, getFirstTurn } from '@/api/turn'
import { startNewChat } from '@/api/chat'
import { useChatHistoryStore } from '@/store/ChatHistory'

export const useTurnHistoryStore = defineStore('turnHistory', {
  state: () => ({
    turn_history: []
  }),
  actions: {
    async initFirstTurn() {
      const res = await getFirstTurn()
      const firstId = res.data.first_turn_id
      const chatHistoryStore = useChatHistoryStore()
      if (firstId) {
        chatHistoryStore.history_id = firstId
        await chatHistoryStore.updateHistoryByHistoryId(firstId)
      }
    },
    async fetchTurnHistory() {
      console.log("Fetching turn history...")
      const res = await getTurnHistory()
      console.log("Turn history fetched:", res.data.turns)
      const turns = res.data?.turns || []
      // 最新的记录放前面
      this.turn_history = [...turns].sort((a, b) => (b?.id ?? 0) - (a?.id ?? 0))
    },

    async startNewTurn(roleId) {
      // 默认角色回退
      const chosenRoleId = roleId || 1
      const res = await startNewChat(chosenRoleId)
      await this.fetchTurnHistory()

      const chatHistoryStore = useChatHistoryStore()
      const newHistoryId = res?.data?.id || res?.data?.success?.id
      console.log("Updating chat history for new turn:", newHistoryId)
      if (newHistoryId) {
        await chatHistoryStore.updateHistoryByHistoryId(newHistoryId)
      }
      return res
    },

    async changeToTurn(turn_id) {
      await this.fetchTurnHistory()
      const chatHistoryStore = useChatHistoryStore()
      await chatHistoryStore.updateHistoryByHistoryId(turn_id)
    }
  }
})
