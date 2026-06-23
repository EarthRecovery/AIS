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

    async def direct_day(self, world_context: dict, directive: str = ""):
        """世界导演：把世界推进「一天」，产出当日结算（全量自主）。

        world_context 提供世界全貌；directive 是用户对这一天的导演指示（可空）。
        返回结构化结算 JSON，由 world_service 落库（事件/记忆/关系/新角色/世界观补充/场景）。
        """
        wv = world_context.get("worldview") or {}
        chars = world_context.get("characters") or []
        rels = world_context.get("relationships") or []
        commons = world_context.get("common_knowledge") or []
        recent = world_context.get("recent_events") or []
        cur_time = world_context.get("in_world_time") or "第1天"

        char_lines = "\n".join(
            f"- {c['name']}：{c.get('summary') or '（无额外信息）'}" for c in chars
        ) or "- （世界中暂无角色）"
        rel_lines = "\n".join(
            f"- {r['from']} → {r['to']}：{r['relation_type']}（好感{r['affinity']}）" for r in rels
        ) or "- （暂无关系）"
        common_lines = "\n".join(f"- {c}" for c in commons) or "- （无）"
        recent_lines = "\n".join(f"- {e}" for e in recent) or "- （无）"

        sys = SystemMessage(content=(
            "你是一个持久世界的「世界导演」。你的任务是把这个世界向前推进『一天』，"
            "像写一段连贯、可信、有因果的剧情演进，并据此结算世界状态的变化。\n"
            "你可以：推进剧情事件、更新角色记忆与认知、改变角色关系、在合理时引入新角色、"
            "补充世界观常识或在完整背景里追加设定、必要时开启一个新场景。\n"
            "要尊重已有设定与因果，变化要适度（一天的体量），不要推翻世界。\n"
            "只输出 JSON，不要任何解释。结构：\n"
            '{"day_summary":"今天发生了什么（一段叙事）",'
            '"events":[{"kind":"action|scene|plot","summary":"事件"}],'
            '"memories":[{"character":"角色名","kind":"memory|fact|observation|belief","content":"该角色记住的","importance":0}],'
            '"relationship_changes":[{"from":"角色名","to":"角色名","relation_type":"friend|rival|...","affinity":-100..100,"reason":"原因"}],'
            '"new_characters":[{"name":"新角色名","description":"设定","personality":["性格"]}],'
            '"worldview_additions":{"common_knowledge":["新常识"],"background_append":"可选，追加到完整背景的文字"},'
            '"scene":{"should_switch":false,"reason":"原因","next":{"name":"新场景名","setting":"设定","participants":["角色名"]}},'
            '"next_time":"下一天的时间标签，如 第2天 清晨"}\n'
            "任何数组都可以为空；should_switch 为 false 时可省略 next；new_characters 仅在剧情确需时才给。"
        ))
        human = HumanMessage(content=(
            f"【世界观·公共设定】\n{wv.get('description') or '（无）'}\n\n"
            f"【世界观·规则】\n{wv.get('rules') or '（无）'}\n\n"
            f"【世界观·完整背景（仅你这个导演可见，用于把握走向）】\n{wv.get('background') or '（无）'}\n\n"
            f"【世界常识】\n{common_lines}\n\n"
            f"【当前角色】\n{char_lines}\n\n"
            f"【当前关系】\n{rel_lines}\n\n"
            f"【近期事件】\n{recent_lines}\n\n"
            f"【当前世界时间】{cur_time}\n\n"
            f"【用户对这一天的导演指示】\n{directive.strip() or '（无，按世界自身逻辑自然推进）'}\n\n"
            "请把世界推进一天，输出结算 JSON。"
        ))
        try:
            resp = await self.llm.ainvoke([sys, human])
            data = _parse_json(getattr(resp, "content", "") or "")
        except Exception:
            data = {}
        data.setdefault("day_summary", "")
        for key in ("events", "memories", "relationship_changes", "new_characters"):
            data.setdefault(key, [])
        data.setdefault("worldview_additions", {})
        data.setdefault("scene", {"should_switch": False})
        return data

    async def open_scene(self, world_context: dict, directive: str = "", prev_summaries=None):
        """世界导演：为当前这一天开启一个新场景（决定地点/情境/在场角色）。"""
        chars = world_context.get("characters") or []
        names = [c["name"] for c in chars]
        char_lines = "\n".join(f"- {c['name']}：{c.get('summary') or ''}" for c in chars) or "-（无）"
        prev = "\n".join(f"- {s}" for s in (prev_summaries or [])) or "-（这是今天第一幕）"
        wv = world_context.get("worldview") or {}
        sys = SystemMessage(content=(
            "你是持久世界的「世界导演」。请为当前这一天开启一个新的场景（一幕戏）。"
            "选择一个地点/情境，并挑选 2 个或以上在场角色，让剧情能自然展开。"
            "只输出 JSON：{\"name\":\"场景名\",\"setting\":\"场景情境(一两句)\",\"participants\":[\"角色名\"]}"
        ))
        human = HumanMessage(content=(
            f"【世界观】{wv.get('description') or ''}\n【背景(仅你可见)】{wv.get('background') or ''}\n"
            f"【可用角色】\n{char_lines}\n【今天已发生的幕】\n{prev}\n"
            f"【导演指示】{directive.strip() or '（无）'}\n请开启下一幕，输出 JSON。"
        ))
        try:
            data = _parse_json(getattr(await self.llm.ainvoke([sys, human]), "content", "") or "")
        except Exception:
            data = {}
        if not data.get("participants"):
            data["participants"] = names[:3]
        data.setdefault("name", "新场景")
        data.setdefault("setting", "")
        return data

    async def judge_round(self, world_context, scene_setting, round_dialogue, characters_state):
        """世界裁判：看完这一轮对话，输出每个在场角色的状态变化 + 本幕/本天是否结束。

        characters_state: [{name, location, stats:{...}}]
        返回 JSON：state_changes / relationship_changes / scene
        """
        cs_lines = "\n".join(
            f"- {c['name']}：位置={c.get('location') or '未知'}，状态={c.get('stats') or {}}"
            for c in characters_state) or "-（无）"
        convo = "\n".join(f"{d['speaker']}：{d['content']}" for d in round_dialogue) or "（无对话）"
        sys = SystemMessage(content=(
            "你是持久世界的「世界裁判」。根据这一轮刚发生的对话，结算每个在场角色的状态变化，"
            "要符合剧情因果、变化适度。可改：记忆、所在地点、获得/失去物品、数值(如 hp/mp/stamina 的增减)、"
            "彼此关系、主观认知。并判断这一幕是否该结束、今天是否该结束。\n"
            "只输出 JSON：\n"
            '{"state_changes":[{"character":"名","memory":"新记住的(可选)","location":"新地点名(可选)",'
            '"stat_deltas":{"hp":-10,"mp":-5}(可选,增减量),"items_gained":["物品"],"items_lost":["物品"],'
            '"belief":"新认知(可选)"}],'
            '"relationship_changes":[{"from":"名","to":"名","relation_type":"...","affinity":-100..100,"reason":"..."}],'
            '"scene":{"should_end":false,"should_end_day":false,"reason":"..."}}\n'
            "任何数组/字段都可省略或为空。stat_deltas 是增减量(负数表示减少)。"
        ))
        human = HumanMessage(content=(
            f"【场景情境】{scene_setting or ''}\n【在场角色当前状态】\n{cs_lines}\n\n"
            f"【这一轮对话】\n{convo}\n\n请结算状态变化，输出 JSON。"
        ))
        try:
            data = _parse_json(getattr(await self.llm.ainvoke([sys, human]), "content", "") or "")
        except Exception:
            data = {}
        data.setdefault("state_changes", [])
        data.setdefault("relationship_changes", [])
        data.setdefault("scene", {"should_end": False, "should_end_day": False})
        return data
