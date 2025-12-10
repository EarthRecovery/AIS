import { defineStore } from 'pinia'
import { sendChatMessage, getCurrentTurnId, getHistoryByTurnId } from '@/api/chat'

export const useChatHistoryStore = defineStore('chatHistory', {
  state: () => ({
    chatHistory: [],
    token_used: 0,
    turn_id: 0
  }),
  actions: {
    addMessage(role, content, turn_id) {
      this.chatHistory.push({ role, content, turn_id })
    },
    clearHistory() {
      this.chatHistory = []
      this.token_used = 0
    },

    async sendMessage(content) {

      // 2. 把用户消息加入历史
      this.addMessage('user', content, this.turn_id)

      // 3. 发送到后端
      const res = await sendChatMessage(content)

      // 假设后端返回 { reply: "...", token_used: ... }
      const reply = res.data.reply

      // 4. assistant 回复加入历史
      this.addMessage('assistant', reply, this.turn_id)
    },

    async getCurrentTurnId() {
      const res = await getCurrentTurnId()
      this.turn_id = res.data.turn_id
      return this.turn_id
    },

    async updateHistoryByTurnId(turn_id) {
      const history_res = await getHistoryByTurnId(turn_id) //获取指定turn_id的对话历史
      this.clearHistory()

      console.log(history_res)

      // 正确字段是 messages，不是 history
      for (const msg of history_res.data.messages) {
        this.addMessage(msg.role, msg.content, turn_id)
      }

      this.token_used = history_res.data.token_used
      this.turn_id = turn_id
    },

    async init() {
      const current_turn_id = await this.getCurrentTurnId()
      this.updateHistoryByTurnId(current_turn_id)
    },
  }
})
