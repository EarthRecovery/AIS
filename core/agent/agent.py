from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    BaseMessage,
    SystemMessage,
    HumanMessage,
    AIMessage,
    ToolMessage,
)
# rag_run / load_role_prompt / base_prompt_run 这三个 *_run 辅助函数用于手动注入
# system 提示(等价于原 create_agent 里 rag/role/base_prompt 三个 @before_model
# middleware 的效果)。流式与非流式都改成手写工具循环,不再使用 create_agent。
from core.agent.middleware.rag import rag_run
from core.agent.role_prompt import load_role_prompt
from core.agent.middleware.base_prompt import base_prompt_run
from core.agent.tools import ALL_TOOLS

class LLMAgent():

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4.1",
            streaming=True,
        )

        # 「绑定了工具」的模型,以及 name -> tool 映射(执行工具时查表)。
        # 流式 / 非流式两条路径共用同一套手写工具循环。
        self.llm_with_tools = self.llm.bind_tools(ALL_TOOLS)
        self.tools_by_name = {t.name: t for t in ALL_TOOLS}
        self.max_tool_rounds = 5

        self.summary_token_limit = 5000

    def _run_tool_calls(self, ai_message) -> List[ToolMessage]:
        """执行一条 AIMessage 里的所有 tool_calls,返回对应的 ToolMessage 列表。"""
        results: List[ToolMessage] = []
        for call in ai_message.tool_calls:
            tool = self.tools_by_name.get(call["name"])
            if tool is None:
                output = f"Error: unknown tool '{call['name']}'"
            else:
                try:
                    output = tool.invoke(call.get("args", {}))
                except Exception as e:  # 工具异常不应中断整轮对话
                    output = f"Error running tool '{call['name']}': {e}"
            results.append(ToolMessage(content=str(output), tool_call_id=call["id"]))
        return results

    def get_response(self, messages, history_id, role_settings) -> str:
        """非流式响应 + 工具调用(手写循环,与流式路径同源)。"""
        role_settings_json = role_settings.to_json() if role_settings else {}
        work = self._build_prompt(messages, role_settings_json)

        for _ in range(self.max_tool_rounds):
            ai = self.llm_with_tools.invoke(work)
            if not ai.tool_calls:
                return ai.content
            work.append(ai)
            work.extend(self._run_tool_calls(ai))

        # 兜底:工具轮数用尽,再普通生成一次最终回答
        return self.llm.invoke(work).content

    @staticmethod
    def _to_message(msg) -> BaseMessage:
        """把 chat_service 传来的 {'role','content'} dict 归一化成 LangChain 消息。"""
        if isinstance(msg, BaseMessage):
            return msg
        role = (msg.get("role") or msg.get("type") or "user") if isinstance(msg, dict) else "user"
        content = msg.get("content", "") if isinstance(msg, dict) else str(msg)
        if role == "system":
            return SystemMessage(content=content)
        if role in ("assistant", "ai"):
            return AIMessage(content=content)
        return HumanMessage(content=content)

    def _build_prompt(self, messages, role_settings_json) -> List[BaseMessage]:
        """组装最终 prompt:base_prompt + role + (可选)RAG context + 归一化后的历史。

        这里手动注入,等价于 create_agent 里 role/base_prompt/rag 三个 middleware 的作用,
        但走流式 + 手写工具循环,所以不经过 agent。
        """
        sys_msgs: List[BaseMessage] = [
            base_prompt_run(),
            SystemMessage(content=load_role_prompt(role_settings_json)),
        ]
        # 历史放在稳定前缀里(base+role+历史),让 OpenAI prompt cache 能按前缀命中。
        tail: List[BaseMessage] = [self._to_message(m) for m in messages]
        # RAG 上下文每轮都不同(基于最新提问),必须放在历史之后,否则会打断可缓存前缀,
        # 导致整段长历史每轮 cache miss。贴近当前提问也更利于模型关联检索内容。
        rag_ctx = rag_run(messages, (role_settings_json or {}).get("rag_name"))
        if rag_ctx:
            tail.append(
                SystemMessage(content=f"Retrieved context (use if relevant):\n{rag_ctx}")
            )
        return [*sys_msgs, *tail]

    async def get_response_astream(self, messages, history_id, role_settings):
        """流式响应 + 工具调用。

        手写 agent 循环(create_agent 的模型节点用 ainvoke,无法逐 token 流式):
          每一轮用绑定了工具的模型 .astream;
          - 若该轮产生 tool_calls(此时文本 content 为空,不会输出给用户),
            就执行对应工具,把 ToolMessage 回灌,进入下一轮;
          - 若该轮产出的是最终文本答案,则逐 token yield 给前端,结束。
        """
        role_settings_json = role_settings.to_json() if role_settings else {}
        work = self._build_prompt(messages, role_settings_json)

        for _ in range(self.max_tool_rounds):
            accumulated = None  # 累积成完整 AIMessageChunk,用于读取 tool_calls
            async for chunk in self.llm_with_tools.astream(work):
                accumulated = chunk if accumulated is None else accumulated + chunk
                content = chunk.content or ""
                if content:
                    yield content

            # 没有工具调用 => 本轮就是最终答案,已经流式输出完毕
            if not accumulated or not accumulated.tool_calls:
                return

            # 有工具调用:执行工具并把结果回灌,继续下一轮
            work.append(accumulated)
            work.extend(self._run_tool_calls(accumulated))

        # 兜底:工具轮数用尽仍未给出最终答案,强制再流式生成一次普通回答
        async for chunk in self.llm.astream(work):
            if chunk.content:
                yield chunk.content


    async def summarize_messages(self, messages: List[BaseMessage]) -> str:
        if not messages:
            return ""

        def _coerce_message(msg: BaseMessage) -> BaseMessage:
            if isinstance(msg, BaseMessage):
                return msg
            if isinstance(msg, dict):
                role = msg.get("role") or msg.get("type") or "user"
                content = msg.get("content", "")
                if isinstance(content, list):
                    content = " ".join(str(part) for part in content)
                if role == "system":
                    return SystemMessage(content=str(content))
                if role == "assistant":
                    from langchain_core.messages import AIMessage
                    return AIMessage(content=str(content))
                from langchain_core.messages import HumanMessage
                return HumanMessage(content=str(content))
            return SystemMessage(content=str(msg))

        summary_llm = ChatOpenAI(model="gpt-4.1", temperature=0)
        summary_prompt = [
            SystemMessage(
                content=(
                    "Summarize the following conversation into concise, durable memory. "
                    "Keep key facts, decisions, names, constraints, and open tasks."
                )
            ),
            *[_coerce_message(m) for m in messages],
        ]
        summary_msg = await summary_llm.ainvoke(summary_prompt)
        return getattr(summary_msg, "content", "") or ""

    # ------------------------------------------------------------------
    # communication：多人格 + 共享世界观
    # ------------------------------------------------------------------
    @staticmethod
    def _perception_block(self_name, perception) -> str:
        """把某角色的感知视图(世界常识 + 私有记忆/认知 + 场景知识)渲染成提示。

        注意：只渲染 content/kind/置信度，绝不暴露 is_true(那是作者元信息)。
        """
        if not perception:
            return ""
        commons = perception.get("common_knowledge") or []
        self_summary = perception.get("self_summary")
        long_term = perception.get("long_term") or []
        short_term = perception.get("short_term") or []
        scene_k = perception.get("scene_knowledge") or []

        def fmt(m):
            tag = m.get("kind", "memory")
            conf = m.get("confidence")
            prefix = f"（{tag}{'，信心'+str(conf) if conf is not None else ''}）"
            return f"- {prefix}{m.get('content','')}"

        lines = [f"以下是「{self_name}」此刻所知道的一切——你只能依据这些信息行动，"
                 "不要使用你不可能知道的事，也不要读取其他角色的内心或私有记忆。"]
        if commons:
            lines.append("【世界常识】\n" + "\n".join(f"- {c}" for c in commons))
        if self_summary:
            lines.append("【你的自我认知（长期）】\n" + self_summary)
        if long_term:
            lines.append("【长期记忆（你印象深刻的事）】\n" + "\n".join(fmt(m) for m in long_term))
        if short_term:
            lines.append("【近期记忆（最近几个场景发生的）】\n" + "\n".join(fmt(m) for m in short_term))
        if scene_k:
            lines.append("【当前场景你已获知】\n" + "\n".join(f"- {s}" for s in scene_k))
        return "\n\n".join(lines)

    def _build_group_prompt(self, persona_settings, worldview_text, scenario, roster, transcript,
                            perception=None):
        """组装某个人格在多人房间里的发言 prompt。

        复用 base_prompt + role_prompt.j2(已含 worldview/scenario 槽位)，
        再叠加「在场角色名单」「只扮演本角色」的群聊规则，最后附上带发言者
        标签的多人对话记录。共享世界观就是这里注入到每个人格 prompt 的同一段文本。
        """
        persona = dict(persona_settings or {})
        if worldview_text:
            persona["worldview"] = worldview_text
        if scenario:
            persona["scenario"] = scenario
        self_name = persona.get("name") or "你"

        roster_lines = "\n".join(
            f"- {r['name']}：{(r.get('description') or '（无额外设定）')}" for r in roster
        ) or "- （只有你一人在场）"

        solo = len([r for r in roster if r.get("name") != self_name]) == 0
        if solo:
            # 单人场景：主角独处/内心戏/单人行动 —— 允许第一人称的动作与心理描写
            rules = (
                "这是一个单人场景：此刻只有你一个人在场。\n"
                f"你扮演「{self_name}」。\n"
                f"- 以「{self_name}」的第一人称演出：可以是内心独白、自言自语，"
                "也可以用括号描写自己的动作与所处环境，推进剧情\n"
                "- 不要凭空让别的角色出现或替别人说话\n"
                f"- 直接演出，不要在开头加「{self_name}：」这样的名字前缀"
            )
        else:
            rules = (
                "这是一个多人角色扮演对话场景，多个角色共处于同一个世界观之下。\n"
                f"在场角色：\n{roster_lines}\n\n"
                f"现在轮到你发言，你只能扮演「{self_name}」。\n"
                f"- 只输出「{self_name}」本人的台词，符合其性格、说话方式与共享世界观\n"
                "- 不要替其他角色或用户发言，不要写旁白或解说\n"
                "- 自然地回应上文、推进剧情，可以与其他在场角色互动\n"
                f"- 直接说台词，不要在台词前加「{self_name}：」这样的名字前缀"
            )

        msgs: List[BaseMessage] = [
            base_prompt_run(),
            SystemMessage(content=load_role_prompt(persona)),
            SystemMessage(content=rules),
        ]
        perception_text = self._perception_block(self_name, perception)
        if perception_text:
            msgs.append(SystemMessage(content=perception_text))
        if transcript:
            lines = "\n".join(f"{t['speaker_name']}：{t['content']}" for t in transcript)
            msgs.append(
                HumanMessage(
                    content=f"【已发生的对话】\n{lines}\n\n请以「{self_name}」的身份接着说："
                )
            )
        else:
            msgs.append(
                HumanMessage(
                    content=f"现在由你「{self_name}」开场，依据世界观与当前场景说出第一句话。"
                )
            )
        return msgs

    async def get_group_response_astream(
        self, persona_settings, worldview_text, scenario, roster, transcript, perception=None
    ):
        """某个人格在房间里的流式发言（群聊不走工具循环，保持轻量）。"""
        work = self._build_group_prompt(
            persona_settings, worldview_text, scenario, roster, transcript, perception
        )
        async for chunk in self.llm.astream(work):
            if chunk.content:
                yield chunk.content

    async def choose_next_speaker(self, roster, transcript, last_speaker=None):
        """导演：根据剧情从在场角色里挑下一个发言者，返回角色名。"""
        names = [r["name"] for r in roster if r.get("name")]
        if not names:
            return None
        if len(names) == 1:
            return names[0]

        tail = transcript[-12:] if transcript else []
        convo = "\n".join(f"{t['speaker_name']}：{t['content']}" for t in tail) or "（暂无对话，需要有人开场）"
        director = ChatOpenAI(model="gpt-4.1", temperature=0)
        msgs = [
            SystemMessage(
                content=(
                    "你是多人对话场景的导演。根据剧情发展，从在场角色中选出下一个"
                    "最适合发言的角色，让对话自然、有来有回。只返回一个角色名，不要解释。"
                )
            ),
            HumanMessage(
                content=(
                    f"在场角色：{('、'.join(names))}\n"
                    f"上一个发言者：{last_speaker or '无'}（尽量不要连续选同一个人）\n\n"
                    f"最近对话：\n{convo}\n\n下一个发言者（只返回角色名）："
                )
            ),
        ]
        try:
            resp = await director.ainvoke(msgs)
            text = (getattr(resp, "content", "") or "").strip()
        except Exception:
            text = ""
        for n in names:
            if n and n in text:
                return n
        # 兜底：轮流，避免连续同一人
        for n in names:
            if n != last_speaker:
                return n
        return names[0]
