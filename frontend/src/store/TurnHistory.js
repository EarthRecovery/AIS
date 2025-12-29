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
      this.turn_history = res.data.turns
    },

    async startNewTurn() {
      const res = await startNewChat()
      await this.fetchTurnHistory()

      const chatHistoryStore = useChatHistoryStore()
      console.log("Updating chat history for new turn:", res.data.id)
      await chatHistoryStore.updateHistoryByHistoryId(res.data.id)
      return res
    },

    async changeToTurn(turn_id) {
      await this.fetchTurnHistory()
      const chatHistoryStore = useChatHistoryStore()
      await chatHistoryStore.updateHistoryByHistoryId(turn_id)
    }
  }
})
