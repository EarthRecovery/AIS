"""记录官 Keeper：多智能体世界的"上帝视角"管理 agent。

职责：
1. 观察一个场景里的对话，决定每个在场角色「学到/记住」了什么 → 产出各自的记忆条目。
2. 决定当前场景是否结束、要切换到哪个新场景、谁在场。

只产出结构化决策(JSON)，由 world/keeper service 落库（写 AgentMemory、切 Scene、记 WorldEvent）。
"""

import json

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI


def _parse_json(text: str) -> dict:
    """容错解析 LLM 返回的 JSON（去掉可能的 ```json 包裹）。"""
    t = (text or "").strip()
    if t.startswith("```"):
        t = t.strip("`")
        if t.lower().startswith("json"):
            t = t[4:]
    start, end = t.find("{"), t.rfind("}")
    if start != -1 and end != -1:
        t = t[start : end + 1]
    try:
        return json.loads(t)
    except Exception:
        return {}


class KeeperAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4.1", temperature=0)

    async def digest_scene(self, world_common, scene_setting, participants, transcript):
        """消化一个场景：产出每个在场角色的新记忆 + 场景切换决策。

        返回:
          {
            "memories": [{"character": 名字, "kind": "...", "content": "...", "importance": 0-5}],
            "scene": {"should_switch": bool, "reason": "...",
                       "next": {"name": "...", "setting": "...", "participants": [名字...]}}
          }
        """
        commons = "\n".join(f"- {c}" for c in world_common) or "（无）"
        names = "、".join(participants) or "（无）"
        convo = "\n".join(f"{t['speaker_name']}：{t['content']}" for t in transcript) or "（场景刚开始，无对话）"

        sys = SystemMessage(content=(
            "你是多智能体世界的「记录官」(Keeper)，拥有上帝视角，负责两件事：\n"
            "1) 根据这一场景里发生的对话，判断每个在场角色各自『学到/记住』了什么——"
            "注意每个角色只可能记住它在场感知到的内容，不同角色记到的可以不同，也可能因立场而产生主观理解。\n"
            "2) 判断这一场景是否该结束、要不要切换到新场景。\n"
            "只输出 JSON，不要任何解释或多余文字。JSON 结构：\n"
            '{"memories":[{"character":"角色名","kind":"memory|fact|observation|belief",'
            '"content":"该角色记住的一句话","importance":0}],'
            '"scene":{"should_switch":false,"reason":"原因",'
            '"next":{"name":"新场景名","setting":"新场景设定","participants":["角色名"]}}}\n'
            "should_switch 为 false 时可省略 next。memories 可以为空数组。"
        ))
        human = HumanMessage(content=(
            f"【世界常识】\n{commons}\n\n"
            f"【当前场景设定】\n{scene_setting or '（无）'}\n\n"
            f"【在场角色】{names}\n\n"
            f"【本场对话】\n{convo}\n\n"
            "请输出 JSON。"
        ))
        try:
            resp = await self.llm.ainvoke([sys, human])
            data = _parse_json(getattr(resp, "content", "") or "")
        except Exception:
            data = {}
        data.setdefault("memories", [])
        data.setdefault("scene", {"should_switch": False})
        return data
