from core.agent.agent import LLMAgent
from core.agent.keeper import KeeperAgent

class LLMClient:

    def __init__(self):
        self.agent = LLMAgent()
        self.keeper = KeeperAgent()
        # self.agent.start_new_turn()

    async def chat(self, message: str, history_id: int, role_settings=None) -> str:
        return self.agent.get_response(message, history_id, role_settings)
    
    async def chat_stream(self, message: str, history_id: int, role_settings=None):
        async for chunk in self.agent.get_response_astream(message, history_id, role_settings):
            yield chunk

    async def summarize_messages(self, messages):
        return await self.agent.summarize_messages(messages)

    # ---- communication：多人格群聊 ----
    async def group_chat_stream(self, persona_settings, worldview_text, scenario, roster, transcript):
        async for chunk in self.agent.get_group_response_astream(
            persona_settings, worldview_text, scenario, roster, transcript
        ):
            yield chunk

    async def choose_next_speaker(self, roster, transcript, last_speaker=None):
        return await self.agent.choose_next_speaker(roster, transcript, last_speaker)

    async def group_chat_stream_perceived(self, persona_settings, worldview_text, scenario,
                                          roster, transcript, perception):
        async for chunk in self.agent.get_group_response_astream(
            persona_settings, worldview_text, scenario, roster, transcript, perception
        ):
            yield chunk

    # ---- Keeper：记忆管控 + 场景切换决策 ----
    async def keeper_digest(self, world_common, scene_setting, participants, transcript):
        return await self.keeper.digest_scene(world_common, scene_setting, participants, transcript)

    # ---- 世界导演：把世界推进一天（每日结算） ----
    async def keeper_direct_day(self, world_context, directive=""):
        return await self.keeper.direct_day(world_context, directive)
    
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
