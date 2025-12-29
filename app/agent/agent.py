import asyncio
from app.agent.middleware.rag import rag_context_middleware, rag_run
from langchain.agents import create_agent, AgentState
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables import RunnableConfig
from typing import Any
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
from app.agent.persona_prompt import PERSONA_PROMPT
from app.agent.middleware.persona import persona_middleware
    

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
                persona_middleware,
                rag_context_middleware,
            ],
            checkpointer=InMemorySaver(),
        )

    def get_response(self, messages, history_id) -> str:

        agent_input = {
            "messages": messages,
        }
        response = self.agent.invoke(agent_input,
            {
                "configurable": {
                    "thread_id": str(history_id),
                }
            }
        )

        content = response["messages"][-1].content
        return content
    
    async def get_response_astream(self, messages):

        # # Build messages from full history (includes current user)
        # messages = messages

        # # Prepend RAG context if available
        # context = rag_run(messages)
        # if context:
        #     messages = [{"role": "system", "content": f"Use the retrieved context:\n{context}"}] + messages

        # assistant_content = ""
        # async for chunk in self.llm.astream(messages):
        #     content = chunk.content
        #     assistant_content += content
        #     yield content

        # content = assistant_content
        state = {
            "messages": list(messages), 
        }

        state = await self._apply_middlewares(state)

        final_messages = state["messages"]

        assistant_content = ""
        async for chunk in self.llm.astream(final_messages):
            content = chunk.content or ""
            assistant_content += content
            yield content

    async def _apply_middlewares(self, state):
        state = self._persona_middleware(state)
        state = await self._rag_middleware(state)
        # state = self._memory_middleware(state)  # 以后加
        return state
    
    async def _rag_middleware(self, state):
        messages = state["messages"]

        context = rag_run(messages)   # 如果以后 async，直接 await

        if not context:
            return state

        rag_msg = SystemMessage(
            content=f"Retrieved context (use if relevant):\n{context}"
        )

        return {
            **state,
            "messages": [rag_msg, *messages],
        }

    def _persona_middleware(self, state):
        persona_msg = SystemMessage(content=PERSONA_PROMPT)

        return {
            **state,
            "messages": [persona_msg, *state["messages"]],
        }
