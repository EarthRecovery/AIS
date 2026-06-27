"""故事导演 Director：STORY（叙事智能）层的核心 agent。

记录官 Keeper 是 WORLD 层的「上帝视角」——它结算「发生了什么」(真值)。
导演 Director 是 STORY 层的「叙事头脑」——它不结算世界，而是回答三件事：

1. 这是什么故事？        → draft_blueprint   (S1 故事蓝图 + 结局目标)
2. 下一步该发生什么戏？  → plan_next_action  (S6 自主故事导演/规划器)
3. 故事讲完了吗？        → judge_ending      (S7 结局判定器)

S1+S6+S7 构成「自己跑向结局」的最小闭环：蓝图给方向，规划器决定下一个戏剧动作并交模拟层
演出，判定器在中心冲突解决/结局条件满足时宣布收束——否则世界会永远演下去而不收束。

导演只产出结构化决策(JSON)；落库与「交模拟层演出」由 modules/narrative 的 service 负责。
真值仍归 Keeper/模拟层，导演不改世界状态，只决定「故事往哪走」。
"""

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

# 复用 Keeper 已有的容错 JSON 解析（去 ```json 包裹 / 截取首尾括号）
from core.agent.keeper import _parse_json
from core.clients.llm_config import CHAT_MODEL
from core.clients.llm_logger import get_llm_logger


class DirectorAgent:
    def __init__(self):
        # 叙事规划要一点发散但不能乱，温度略高于 Keeper(0) 但偏保守
        self.llm = ChatOpenAI(model=CHAT_MODEL, temperature=0.4,
                              callbacks=[get_llm_logger()], tags=["director"])

    # ---- 上下文拼装(三个方法共用的世界态文本) ----
    @staticmethod
    def _world_block(ctx: dict) -> str:
        wv = ctx.get("worldview") or {}
        chars = ctx.get("characters") or []
        rels = ctx.get("relationships") or []
        recent = ctx.get("recent_events") or []
        outline = ctx.get("outline") or []
        beat = ctx.get("beat") or {}

        char_lines = "\n".join(
            f"- {c['name']}：{c.get('summary') or '（无额外信息）'}" for c in chars
        ) or "-（世界中暂无角色）"
        rel_lines = "\n".join(
            f"- {r['from']} → {r['to']}：{r['relation_type']}（好感{r.get('affinity')}）" for r in rels
        ) or "-（暂无关系）"
        recent_lines = "\n".join(f"- {e}" for e in recent) or "-（无）"
        outline_lines = "\n".join(
            f"  {i+1}. {b.get('title','')}：{b.get('goal','')}" for i, b in enumerate(outline)
        ) or "  （无大纲）"
        beat_block = (f"【当前章节节拍】{beat.get('title','')}：{beat.get('goal','')}\n"
                      if beat else "")
        return (
            f"【世界观·公共设定】\n{wv.get('description') or '（无）'}\n\n"
            f"【世界观·规则】\n{wv.get('rules') or '（无）'}\n\n"
            f"【世界观·完整背景（仅导演可见，用于把握走向）】\n{wv.get('background') or '（无）'}\n\n"
            f"【当前角色】\n{char_lines}\n\n"
            f"【当前关系】\n{rel_lines}\n\n"
            f"【章节大纲】\n{outline_lines}\n\n"
            f"{beat_block}"
            f"【近期事件】\n{recent_lines}\n\n"
            f"【当前世界时间】{ctx.get('in_world_time') or ''}\n"
        )

    @staticmethod
    def _blueprint_block(bp: dict) -> str:
        if not bp:
            return "【故事蓝图】（尚未制定）\n"
        endings = bp.get("intended_endings") or []
        end_lines = "\n".join(
            f"  - {e.get('title','')}：{e.get('summary','')}\n    收束条件：" +
            ("；".join(e.get("conditions") or []) or "（未列）")
            for e in endings
        ) or "  （未设定结局）"
        return (
            f"【中心前提】{bp.get('premise') or '（未定）'}\n"
            f"【中心冲突】{bp.get('central_conflict') or '（未定）'}\n"
            f"【主题】{bp.get('theme') or '（未定）'}\n"
            f"【弧线位置】{bp.get('dramatic_phase') or 'setup'}"
            f"（目标张力 {bp.get('tension_target')}/100）\n"
            f"【意图结局 / 可接受结局集】\n{end_lines}\n"
        )

    async def _run(self, sys_text: str, human_text: str) -> dict:
        try:
            resp = await self.llm.ainvoke([SystemMessage(content=sys_text),
                                           HumanMessage(content=human_text)])
            return _parse_json(getattr(resp, "content", "") or "")
        except Exception:
            return {}

    # ---- S1：故事蓝图 + 结局目标 ----
    async def draft_blueprint(self, world_context: dict, directive: str = "") -> dict:
        """读世界观/角色/背景，凝练出这个世界「该讲的故事」与「要走向的结局」。

        这是北极星：没有它，"自主推进直到结局"就没有方向也没有终点。
        """
        sys = SystemMessage(content=(
            "你是小说的「故事设计师」。给你一个已建好的世界（世界观/角色/关系/背景秘密），"
            "你要从中提炼出一个具体、有张力、能收束到结局的【故事蓝图】——即在这个世界里"
            "*值得讲的那个故事*。不要复述世界设定，要做叙事判断：中心冲突是什么、主题是什么、"
            "故事可以走向哪几种令人满意的结局。\n"
            "给 2~3 个【可接受结局】，每个都配上『可被客观验证的收束条件』"
            "(例如：某角色做出某抉择 / 某秘密被揭穿 / 某对抗有了胜负)，"
            "这些条件之后会被结局判定器逐条核对。\n"
            "只输出 JSON，不要解释：\n"
            '{"premise":"一句话中心前提","central_conflict":"贯穿全篇的根本对抗",'
            '"theme":"主题","dramatic_phase":"setup",'
            '"tension_target":30,'
            '"intended_endings":[{"title":"结局名","summary":"该结局是什么样",'
            '"conditions":["可验证的收束条件1","条件2"]}]}'
        ))
        human = HumanMessage(content=(
            self._world_block(world_context) +
            f"\n【额外要求/方向】{directive.strip() or '（无，按世界自身的张力自然提炼）'}\n"
            "请输出故事蓝图 JSON。"
        ))
        data = await self._run(sys.content, human.content)
        data.setdefault("premise", "")
        data.setdefault("central_conflict", "")
        data.setdefault("theme", "")
        data.setdefault("dramatic_phase", "setup")
        data.setdefault("tension_target", 30)
        data.setdefault("intended_endings", [])
        return data

    # ---- S6：自主故事导演 / 规划器 ----
    async def plan_next_action(self, story_state: dict, directive: str = "") -> dict:
        """评估当前故事状态 → 决定下一个【戏剧动作】，并产出交给模拟层的导演指示。

        story_state = {"blueprint": {...}, "world": {<同 _world_block 的 ctx>}}
        action_type：
          introduce(引入新冲突/角色/线索) / escalate(升级既有冲突) /
          complicate(增加复杂度或代价) / twist(反转/揭露) / converge(向结局收束)
        directive 是给模拟层 open_scene 的自然语言指示——这是 STORY→WORLD 的接口。
        """
        bp = story_state.get("blueprint") or {}
        ctx = story_state.get("world") or {}
        sys = SystemMessage(content=(
            "你是故事的「自主导演」。你已经有一份【故事蓝图】(中心冲突+结局目标)和【当前世界态】。"
            "你的工作不是写对话，而是做一个**叙事节奏决策**：评估故事此刻的位置(铺垫/升级/高潮/收束)、"
            "中心冲突推进了多少、离结局还差哪些条件，然后决定**下一幕该发生什么性质的戏**，"
            "好让故事朝结局推进而不是原地打转或随机漂移。\n"
            "在合适的时候要敢于升级冲突、制造反转、提高代价；当结局条件大多已满足时要转向 converge(收束)。\n"
            "动作类型只能是：introduce / escalate / complicate / twist / converge。\n"
            "只输出 JSON：\n"
            '{"assessment":"对当前故事状态的一句话判断(在哪、缺什么)",'
            '"action_type":"escalate",'
            '"rationale":"为什么此刻该做这个动作",'
            '"pov":"建议作为本幕视角/核心的角色名(可空)",'
            '"scene_function":"这一幕在故事里承担的戏剧功能",'
            '"directive":"交给模拟层开场的自然语言导演指示(具体到这一幕要往哪推)",'
            '"new_phase":"若该推进弧线位置则给新的 setup|rising|climax|resolution，否则省略",'
            '"tension_target":55}'
        ))
        human = HumanMessage(content=(
            self._blueprint_block(bp) + "\n" + self._world_block(ctx) +
            f"\n【用户对下一步的额外指示】{directive.strip() or '（无，按故事自身逻辑推进）'}\n"
            "请决定下一个戏剧动作，输出 JSON。"
        ))
        data = await self._run(sys.content, human.content)
        data.setdefault("assessment", "")
        data.setdefault("action_type", "escalate")
        data.setdefault("rationale", "")
        data.setdefault("scene_function", "")
        data.setdefault("directive", "")
        return data

    # ---- S7：结局判定器 ----
    async def judge_ending(self, story_state: dict) -> dict:
        """对照蓝图的结局条件核查当前世界态，判断故事是否已抵达(某个可接受)结局。

        没有它，自主循环永不终止。它逐条核对结局条件，给出是否完成 + 还差什么。
        """
        bp = story_state.get("blueprint") or {}
        ctx = story_state.get("world") or {}
        sys = SystemMessage(content=(
            "你是故事的「结局判定器」。你拿到【故事蓝图】里设定的若干【可接受结局】及其"
            "『收束条件』，以及【当前世界态】(已发生的事件、角色现状、关系)。\n"
            "你要冷静、严格地逐条核对：中心冲突是否已经有了结果？哪个结局的收束条件已**全部**满足？"
            "不要因为'差不多了'就判定完成——只有某个结局的条件确实都达成，才算抵达结局。\n"
            "若已抵达，指出是哪个结局、哪些条件满足；若未抵达，列出仍未满足的关键条件(供导演继续推进)。\n"
            "needs_epilogue：即便中心冲突已解决，是否还需要一段尾声来收余韵/收支线。\n"
            "只输出 JSON：\n"
            '{"completed":false,'
            '"which_ending":"若完成，命中的结局名，否则空",'
            '"satisfied":["已满足的收束条件"],'
            '"unmet":["仍未满足的关键条件"],'
            '"needs_epilogue":false,'
            '"reason":"判断理由(一两句)"}'
        ))
        human = HumanMessage(content=(
            self._blueprint_block(bp) + "\n" + self._world_block(ctx) +
            "\n请严格核对结局条件，输出判定 JSON。"
        ))
        data = await self._run(sys.content, human.content)
        data.setdefault("completed", False)
        data.setdefault("which_ending", "")
        data.setdefault("satisfied", [])
        data.setdefault("unmet", [])
        data.setdefault("needs_epilogue", False)
        data.setdefault("reason", "")
        return data
