from fastapi import Depends
from app.infra.llm_client import LLMClient
from app.services.deps import get_llm_client

class TurnService:
    def __init__(self, llm: LLMClient = Depends(get_llm_client)):
        self.llm = llm

    async def get_turn_list(self):
        turn_history = await self.llm.show_all_turn_data()
        turn_list = []
        for turn_id, history in turn_history.items():
            turn_list.append({
                "turn_id": turn_id,
                "summary": history.summary,
            })
        return turn_list
    
    async def change_to_turn(self, turn_id: int):
        return await self.llm.change_to_turn(turn_id)
