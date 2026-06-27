"""叙事 / 编剧 Agent。

站在「作者」视角，为当前剧本节拍生成『剧本 / 节奏』(script)，交给世界裁判(Keeper)按它
逐轮把控推进。它与 Keeper 之间是**有意的上下文隔离**：

  叙事 agent（计划层）  ── script ──▶  Keeper（运行层）  ── 可见结果 ──▶  角色（演员）
        ▲                                  ▲                                    │
        └──── 故事梗概(已沉淀，摘要) ────────┘◀──────── say/do/think(全量) ───────┘

- 叙事 agent 只看【计划层】：世界设定 + 角色花名册(公开摘要 + 当前伤情/生死) + 关系网
  + 当前目标 + 故事梗概(已沉淀的近期事件)。
- 它【看不到】实时逐轮对话、角色私有心声(think)、每轮数值增减——那些只属于 Keeper。
- 产出 script（这一幕怎么起承转合、节奏快慢、关键转折、收束条件），不写台词、不结算数值。
"""

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from core.clients.llm_config import CHAT_MODEL
from core.clients.llm_logger import get_llm_logger


class NarrativeAgent:
    def __init__(self):
        # 略带温度：剧本需要一点创造力，但仍受目标与设定约束
        self.llm = ChatOpenAI(model=CHAT_MODEL, temperature=0.4,
                              callbacks=[get_llm_logger()], tags=["narrative"])

    async def write_script(self, narrative_context, directive=""):
        wv = narrative_context.get("worldview") or {}
        chars = narrative_context.get("characters") or []
        rels = narrative_context.get("relationships") or []
        beat = narrative_context.get("beat") or {}
        commons = narrative_context.get("common_knowledge") or []
        recent = narrative_context.get("recent_events") or []

        roster = "\n".join(
            f"- {c['name']}：{c.get('summary') or '（无摘要）'}" for c in chars) or "（无）"
        rel_lines = "\n".join(
            f"- {r['from']} → {r['to']}：{r.get('relation_type') or ''}(好感{r.get('affinity')})"
            for r in rels) or "（无）"
        digest = "\n".join(f"- {e}" for e in recent[-8:]) or "（暂无）"

        sys = SystemMessage(content=(
            "你是「叙事 / 编剧」。站在作者视角，为【当前节拍】写一份简洁有力的『剧本 / 节奏』，"
            "供世界裁判(Keeper)据此把控每一轮的推进。你只规划『怎么演、节奏、关键转折、收束条件』，"
            "【不要】替角色写台词，【不要】替裁判结算数值或指定具体伤害。\n"
            "这是一个【长篇多章】的故事——你写的不是孤立一幕，而是贯穿全篇长线里的当前这一章。\n"
            "【核心：人物弧光】写本章剧本前，先结合【故事梗概】里已发生的，判断每个在场角色【此刻处在其人物弧光的哪一步】"
            "(设定→发展→动摇→转折→落点)；让本章承担起推进某些角色弧光的功能——谁成长、谁堕落、谁的信念被考验、"
            "谁迎来转折或代价。保持与前文的连续与递进，不要原地打转、也不要每章都重复同样的处境。\n"
            "输出要求：4–7 行，点明：①开场态势 ②中段如何升级 ③高潮 / 关键转折(此处主要推进谁的弧光、付出什么代价) "
            "④收束条件(达成什么即结束本幕) ⑤一句话注明【本章主要服务于哪些角色的弧光】。明确节奏，避免拖沓。"
        ))
        human = HumanMessage(content=(
            f"【世界观】{wv.get('description', '')}｜规则：{wv.get('rules', '')}\n"
            f"【世界常识】{('；'.join(commons)) or '（无）'}\n"
            f"【角色花名册（含当前伤情 / 生死）】\n{roster}\n"
            f"【关系网】\n{rel_lines}\n"
            f"【故事梗概（近期已发生）】\n{digest}\n"
            f"【当前节拍】{beat.get('title', '')}：{beat.get('goal', '')}\n"
            f"【作者额外指示】{directive or '（无）'}\n\n"
            "请输出这一幕的『剧本 / 节奏』（纯文本，3–6 行）。"
        ))
        try:
            return (getattr(await self.llm.ainvoke([sys, human]), "content", "") or "").strip()
        except Exception:
            return ""
