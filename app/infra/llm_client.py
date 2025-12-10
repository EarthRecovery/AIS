from app.agent.agent import LLMAgent

class LLMClient:
    
    def __init__(self):
        self.agent = LLMAgent()
        # self.agent.start_new_turn()

    async def chat(self, message: str):
        # 真实情况这里会调 OpenAI / vLLM
        return self.agent.get_response(message)
    
    async def start_new_chat(self):
        self.agent.start_new_turn()
        return True
    
    async def delete_chat(self, chat_id: int):
        result = self.agent.delete_turn(chat_id)
        return result
    
    async def show_all_turn_data(self):
        return self.agent.show_all_turn_data()
    
    async def change_to_turn(self, turn_id: int):
        result = self.agent.change_to_turn(turn_id)
        return result