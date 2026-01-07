from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import json
from tokenize import String
from langchain.agents.middleware import AgentState, before_model
from app.rag.models.openai import OpenAIModel
from langchain_core.messages import SystemMessage

from langchain_core.messages import BaseMessage

@before_model
def debug_prompt_middleware(state: AgentState, runtime):
    messages = state.get("messages", [])

    print("\n================ FINAL PROMPT TO LLM ================")
    for i, msg in enumerate(messages):

        # 情况 1：BaseMessage（HumanMessage / AIMessage / SystemMessage）
        if isinstance(msg, BaseMessage):
            role = msg.type.upper()
            content = msg.content

        # 情况 2：dict（中间态）
        elif isinstance(msg, dict):
            role = msg.get("role", "UNKNOWN").upper()
            content = msg.get("content")

        else:
            role = type(msg).__name__
            content = str(msg)

        print(f"\n--- [{i}] {role} ---")
        print(content)

    print("\n=====================================================\n")
    return None

