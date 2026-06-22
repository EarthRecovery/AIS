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
