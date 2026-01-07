from app.agent.agent import LLMAgent

class LLMClient:
    
    def __init__(self):
        self.agent = LLMAgent()
        # self.agent.start_new_turn()

    async def chat(self, message: str, history_id: int, role_settings=None) -> str:
        return self.agent.get_response(message, history_id, role_settings)
    
    async def chat_stream(self, message: str, history_id: int, role_settings=None):
        async for chunk in self.agent.get_response_astream(message, history_id, role_settings):
            yield chunk
    
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