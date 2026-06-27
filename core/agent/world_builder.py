"""世界生成器 Agent：根据用户一句话需求，生成一个可供推演的完整世界规格(JSON)。

产出：世界观 + 文风 + 主要角色(含人设/数值/状态) + 关系网 + 初始地点 + 初始物品
     + 粗粒度里程碑(3-5 个时间锚点，每个写清该时的主要冲突与角色处境，中间留给剧情自由生成)。
"""

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from core.agent.keeper import _parse_json
from core.clients.llm_config import CHAT_MODEL
from core.clients.llm_logger import get_llm_logger


class WorldBuilderAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model=CHAT_MODEL, temperature=0.7,
                              callbacks=[get_llm_logger()], tags=["world_builder"])

    async def build(self, prompt: str) -> dict:
        sys = SystemMessage(content=(
            "你是「世界生成器」。根据用户一句话需求，设计一个可供多智能体推演的完整世界。"
            "所有字段用中文，只输出 JSON：\n"
            '{"worldview":{"name":"世界名","description":"世界观(2-4句:时代/地点/基调)",'
            '"rules":"世界规则与设定要点","background":"作者视角的隐藏背景(可含真相，角色不一定知道)"},'
            '"style_guide":"叙述文风(一句话)",'
            '"characters":[{"name":"名","persona":"一句话人设(身份/性格/说话方式)",'
            '"stats":{"hp":100,"stamina":80},"condition":"显著状态或空"}],'
            '"relationships":[{"from":"名","to":"名","relation_type":"如 师徒/仇敌/恋人/战友",'
            '"affinity":-100至100的整数,"notes":"一句话"}],'
            '"locations":[{"name":"地点","description":"一句话"}],'
            '"items":[{"name":"物品","description":"一句话","owner":"持有的角色名或留空"}],'
            '"milestones":[{"title":"阶段名","at_chapter":数字,"main_conflict":"该节点的主要冲突",'
            '"character_states":"该节点各主要角色的处境(一两句)"}]}\n'
            "要求：3-6 个主要角色，彼此关系要有张力(盟友/对立/纠葛)；3-6 个地点；2-5 件关键物品；"
            "milestones 必须是【粗粒度】——只给 3-5 个时间锚点(如第1/8/16/24章)，"
            "每个锚点写清那时的主要冲突与各角色处境，锚点之间留白给剧情自由生成，【不要逐章细化】。"
            "只输出 JSON，不要解说。"
        ))
        human = HumanMessage(content=f"用户需求：{prompt}\n\n请生成这个世界的 JSON。")
        try:
            return _parse_json(getattr(await self.llm.ainvoke([sys, human]), "content", "") or "")
        except Exception:
            return {}
