from fastapi import Depends
from app.infra.llm_client import LLMClient
from app.services.deps import get_llm_client

class ChatService:
    def __init__(self, llm: LLMClient = Depends(get_llm_client)):
        self.llm = llm

    async def chat(self, msg: str):
        reply = await self.llm.chat(msg)
        return reply
    
    async def chat_stream(self, msg: str):
        async for chunk in self.llm.chat_stream(msg):
            yield chunk
    
    async def start_new_chat(self):
        return await self.llm.start_new_chat()
    
    async def delete_chat(self, chat_id: int):
        return await self.llm.delete_chat(chat_id)
    
    async def show_all_turn_data(self):
        return await self.llm.show_all_turn_data()
    
    async def get_current_turn_id(self):
        return self.llm.agent.turn_id
    
    
