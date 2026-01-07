import asyncio
from app.agent.middleware.rag import rag_context_middleware, rag_run
from app.agent.role_prompt import load_role_prompt
from langchain.agents import create_agent, AgentState
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables import RunnableConfig
from typing import Any, TypedDict, List
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional, Dict, Any
import time
from langchain_openai import ChatOpenAI
from sqlalchemy import select
from app.db import SessionLocal
from app.models.history import History as HistoryModel
from app.models.message import Message as MessageModel
from langchain_core.messages import SystemMessage
from app.agent.base_prompt import BASE_PROMPT
from app.agent.middleware.base_prompt import base_prompt_run, base_prompt_middleware
from app.agent.middleware.role import role_prompt_middleware as role_middleware
from app.agent.middleware.debug import debug_prompt_middleware
    
from langchain_core.messages import BaseMessage

class MyAgentState(TypedDict, total=False):
    messages: List[BaseMessage]
    role_settings: dict 

class LLMAgent():

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4.1",
            streaming=True,
        )

        self.agent = create_agent(
            self.llm,
            tools=[],
            middleware=[
                role_middleware,
                base_prompt_middleware,
                rag_context_middleware,
                debug_prompt_middleware,
            ],
            checkpointer=InMemorySaver(),
            state_schema=MyAgentState,
        )

    def get_response(self, messages, history_id, role_settings) -> str:

        agent_input = {
            "messages": messages,
            "role_settings": role_settings.to_json()
        }
        response = self.agent.invoke(
            agent_input,
            {
                "configurable": {
                    "thread_id": str(history_id),
                }
            }
        )

        content = response["messages"][-1].content
        return content
    
    async def get_response_astream(self, messages, history_id, role_settings):

        state = {
            "messages": list(messages), 
            "role_settings": role_settings.to_json()
        }

        state = await self._apply_middlewares(state)

        final_messages = state["messages"]
        # self._log_prompt_messages(final_messages)

        assistant_content = ""
        async for chunk in self.llm.astream(final_messages):
            content = chunk.content or ""
            assistant_content += content
            yield content

    async def _apply_middlewares(self, state):
        state = self._role_middleware(state, runtime=None)
        state = self._base_prompt_middleware(state)
        state = await self._rag_middleware(state)
        # state = self._memory_middleware(state)  # 以后加
        return state
    
    async def _rag_middleware(self, state):
        messages = state["messages"]

        context = rag_run(messages, state.get("identity", None))   # 如果以后 async，直接 await

        if not context:
            return state

        rag_msg = SystemMessage(
            content=f"Retrieved context (use if relevant):\n{context}"
        )

        return {
            **state,
            "messages": [rag_msg, *messages],
        }
    
    def _role_middleware(self, state, runtime):
        role_settings = state.get("role_settings") if isinstance(state, dict) else None

        prompt = load_role_prompt(role_settings)
        role_msg = SystemMessage(content=prompt)

        return {
            **state,
            "messages": [role_msg, *state["messages"]],
        }

    def _base_prompt_middleware(self, state):
        base_prompt_msg = base_prompt_run()

        return {
            **state,
            "messages": [base_prompt_msg, *state["messages"]],
        }

    def _log_prompt_messages(self, messages):
        print("[LLM][prompt] Messages before LLM output:")
        for idx, msg in enumerate(messages):
            role = getattr(msg, "type", None) or getattr(msg, "role", None)
            content = getattr(msg, "content", None)
            if content is None and isinstance(msg, dict):
                content = msg.get("content", "")
            print(f"  {idx}. ({role}) {content}")
