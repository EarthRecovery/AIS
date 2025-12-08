from fastapi import Depends
from app.infra.llm_client import LLMClient
from functools import lru_cache

@lru_cache()
def get_llm_client():
    return LLMClient()

class ChatService:
    def __init__(self, llm: LLMClient = Depends(get_llm_client)):
        self.llm = llm

    async def chat(self, msg: str):
        reply = await self.llm.chat(msg)
        return reply
    
    async def start_new_chat(self):
        return await self.llm.start_new_chat()
    
    async def delete_chat(self, chat_id: int):
        return await self.llm.delete_chat(chat_id)
    
    async def show_all_turn_data(self):
        return await self.llm.show_all_turn_data()