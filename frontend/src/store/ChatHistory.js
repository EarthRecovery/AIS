import { defineStore } from 'pinia'
import { sendChatMessage, getHistoryByHistoryId, streamChatMessage } from '@/api/chat'

export const useChatHistoryStore = defineStore('chatHistory', {
  state: () => ({
    chatHistory: [],
    token_used: 0,
    history_id: -1
  }),
  actions: {
    addMessage(role, content, history_id) {
      this.chatHistory.push({ role, content, history_id })
    },
    normalizeText(text) {
      let value = text != null ? String(text) : ''
      value = value.replace(/\/n/g, '\n\n')
      return value
    },
    clearHistory() {
      this.chatHistory = []
      this.token_used = 0
    },

    async sendMessage(content) {

      // 2. 把用户消息加入历史
      this.addMessage('user', content, this.history_id)

      // 3. 发送到后端（流式）
      // 先占位 assistant 消息，后续增量填充
      const assistantIndex = this.chatHistory.length
      this.addMessage('assistant', '', this.history_id)

      try {
        const fullReply = await streamChatMessage(content, this.history_id, (delta) => {
          // 追加增量
          this.chatHistory[assistantIndex].content += this.normalizeText(delta)
        })
        // 确保最终内容完整
        this.chatHistory[assistantIndex].content = this.normalizeText(fullReply)
      } catch (err) {
        // 失败时写入错误提示
        this.chatHistory[assistantIndex].content = '对话失败，请重试'
        console.error('Stream chat failed', err)
      }
    },

    async updateHistoryByHistoryId(history_id) {
      const history_res = await getHistoryByHistoryId(history_id) //获取指定history_id的对话历史
      console.log("Fetched history for history_id", history_id, history_res)
      this.clearHistory()

      if (history_res.data.length != 0) {
        for (const msg of history_res.data) {
          this.addMessage(msg.role, msg.content, history_id)
        }
      }

      this.history_id = history_id

      this.token_used = history_res.data.token_used
      this.history_id = history_id
    },
  }
})
