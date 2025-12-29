import { defineStore } from 'pinia'
import { getTurnHistory} from '@/api/turn'
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
      await this.fetchTurnHistory()
      const chatHistoryStore = useChatHistoryStore()
      await chatHistoryStore.updateHistoryByHistoryId(turn_id)
    }
  }
})
