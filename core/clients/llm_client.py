from core.agent.agent import LLMAgent
from core.agent.director import DirectorAgent
from core.agent.keeper import KeeperAgent
from core.agent.narrative import NarrativeAgent
from core.agent.writing import WritingAgent
from core.agent.world_builder import WorldBuilderAgent

class LLMClient:

    def __init__(self):
        self.agent = LLMAgent()
        self.keeper = KeeperAgent()
        self.director = DirectorAgent()
        self.narrative = NarrativeAgent()
        self.writing = WritingAgent()
        self.world_builder = WorldBuilderAgent()
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
                                          roster, transcript, perception, allow_actions=False):
        async for chunk in self.agent.get_group_response_astream(
            persona_settings, worldview_text, scenario, roster, transcript, perception,
            allow_actions=allow_actions,
        ):
            yield chunk

    # ---- Keeper：记忆管控 + 场景切换决策 ----
    async def keeper_digest(self, world_common, scene_setting, participants, transcript):
        return await self.keeper.digest_scene(world_common, scene_setting, participants, transcript)

    # ---- 世界导演：把世界推进一天（每日结算） ----
    async def keeper_direct_day(self, world_context, directive=""):
        return await self.keeper.direct_day(world_context, directive)

    # ---- 真实模拟：开场景 + 每轮世界裁判 ----
    async def keeper_open_scene(self, world_context, directive="", prev_scene=None):
        return await self.keeper.open_scene(world_context, directive, prev_scene)

    async def keeper_judge_round(self, world_context, scene_setting, round_dialogue, characters_state,
                                 script=None, round_index=0):
        return await self.keeper.judge_round(world_context, scene_setting, round_dialogue, characters_state,
                                             script=script, round_index=round_index)

    # ---- 叙事/编剧：为当前节拍生成剧本节奏(隔离上下文，不含实时对话/心声) ----
    async def narrative_write_script(self, narrative_context, directive=""):
        return await self.narrative.write_script(narrative_context, directive)

    # ---- 世界生成：一句话需求 → 完整世界规格 ----
    async def world_build(self, prompt):
        return await self.world_builder.build(prompt)

    # ---- 写作/成稿：把章节推演渲染成小说散文 / 章节摘要 ----
    async def writing_summarize_chapter(self, chapter):
        return await self.writing.summarize_chapter(chapter)

    async def writing_write_chapter(self, chapter, style_guide="", prev_summary=""):
        return await self.writing.write_chapter(chapter, style_guide, prev_summary)

    async def keeper_consolidate(self, char_name, self_summary, mem_texts):
        return await self.keeper.consolidate_memory(char_name, self_summary, mem_texts)

    async def keeper_write_outline(self, world_context, directive=""):
        return await self.keeper.write_outline(world_context, directive)

    async def keeper_write_outline_stream(self, world_context, directive=""):
        async for ev in self.keeper.write_outline_stream(world_context, directive):
            yield ev

    # ---- 故事导演（STORY 层）：S1 蓝图 / S6 规划 / S7 结局判定 ----
    async def director_draft_blueprint(self, world_context, directive=""):
        return await self.director.draft_blueprint(world_context, directive)

    async def director_plan_next(self, story_state, directive=""):
        return await self.director.plan_next_action(story_state, directive)

    async def director_judge_ending(self, story_state):
        return await self.director.judge_ending(story_state)
    
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
