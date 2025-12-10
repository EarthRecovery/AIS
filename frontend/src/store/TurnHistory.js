import { defineStore } from 'pinia'
import { getTurnHistory, agentChangeToTurn } from '@/api/turn'
import { startNewChat } from '@/api/chat'
import { useChatHistoryStore } from '@/store/ChatHistory'

export const useTurnHistoryStore = defineStore('turnHistory', {
  state: () => ({
    turn_history: []
  }),
  actions: {
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
      await chatHistoryStore.init()
      return res
    },

    async changeToTurn(turn_id) {
      if (!this.turn_history.find(turn => turn.turn_id === turn_id)) {
        throw new Error(`Turn ID ${turn_id} not found in turn history`)
      }
      await agentChangeToTurn(turn_id)
      await this.fetchTurnHistory()
      const chatHistoryStore = useChatHistoryStore()
      await chatHistoryStore.updateHistoryByTurnId(turn_id)
    }
  }
})
