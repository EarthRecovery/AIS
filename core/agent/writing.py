"""写作 / 成稿 Agent（MANUSCRIPT 层）。

站在「作者」全知视角，把一个章节的推演记录（场景 + 台词/动作/心理/旁白 + 关键事件）
渲染成连贯的小说散文；也能只产出章节摘要。

它是三层架构里最上面的成稿层：会用到角色的私有心声(think)——内心独白正是在写作层
才展开成文字的地方（叙事/角色层都看不到别人的 think，写作层作为作者可以）。
"""

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from core.clients.llm_config import WRITING_MODEL
from core.clients.llm_logger import get_llm_logger

_KIND_LABEL = {"say": "台词", "do": "动作", "think": "心声", "narration": "旁白"}


class WritingAgent:
    def __init__(self):
        # 成稿需要文采，温度高一些
        self.llm = ChatOpenAI(model=WRITING_MODEL, temperature=0.6,
                              callbacks=[get_llm_logger()], tags=["writing"])

    @staticmethod
    def _render_material(chapter):
        lines = []
        for sc in chapter.get("scenes", []):
            lines.append(f"## 场景：{sc.get('name', '')}")
            if sc.get("scenario"):
                lines.append(f"（情境：{sc['scenario']}）")
            for m in sc.get("lines", []):
                kind = m.get("kind") or "say"
                sp = m.get("speaker", "")
                if kind == "narration":
                    lines.append(f"〔旁白〕{m.get('content', '')}")
                else:
                    lines.append(f"[{_KIND_LABEL.get(kind, '台词')}] {sp}：{m.get('content', '')}")
        return "\n".join(lines) or "（本章无内容）"

    async def summarize_chapter(self, chapter):
        material = self._render_material(chapter)
        sys = SystemMessage(content=(
            "你是小说编辑。把下面一个章节的推演记录，浓缩成一段简洁客观的【章节摘要】(150 字以内)，"
            "交代关键情节、转折与结局即可，不要逐句复述、不要评论。"))
        human = HumanMessage(content=(
            f"【章节】{chapter.get('label', '')}\n【本章目标】{chapter.get('goal', '')}\n\n"
            f"【推演记录】\n{material}\n\n请输出章节摘要。"))
        try:
            return (getattr(await self.llm.ainvoke([sys, human]), "content", "") or "").strip()
        except Exception:
            return ""

    async def write_chapter(self, chapter, style_guide="", prev_summary=""):
        material = self._render_material(chapter)
        sys = SystemMessage(content=(
            "你是小说作者。把下面这一章的推演记录改写成一章【连贯的小说散文】：\n"
            "- 台词写成人物对白；动作写成动作与场面描写；心声写成人物的内心独白；旁白自然融入叙述。\n"
            "- 情节、因果、人物关系与结局必须与记录一致，不要新增重大情节；但可补充环境、神态、"
            "节奏等血肉，让文字有小说质感。\n"
            "- 第三人称、过去时；分段流畅。直接输出正文，不要加标题、不要解说。"
            + (f"\n- 文风要求：严格贴合——{style_guide}" if style_guide else "")))
        human = HumanMessage(content=(
            (f"【前情提要】{prev_summary}\n\n" if prev_summary else "")
            + f"【本章】{chapter.get('label', '')}\n【本章目标】{chapter.get('goal', '')}\n\n"
            f"【推演记录】\n{material}\n\n请把本章写成小说散文。"))
        try:
            return (getattr(await self.llm.ainvoke([sys, human]), "content", "") or "").strip()
        except Exception:
            return ""
