
from app.agent.middleware.rag import rag_context_middleware
from langchain.agents import create_agent, AgentState
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables import RunnableConfig
from typing import Any
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional, Dict, Any
import time

@dataclass
class Message:
    role: str             
    content: str
    turn_id: int
    timestamp: float = time.time()
    meta: Optional[Dict[str, Any]] = None

class History:

    def __init__(self):
        self.messages: list[Message] = []
        self.token_used: int = 0
        self.summary: str = ""

    def add(self, msg: Message):
        self.messages.append(msg)

    def get_messages(self):
        return self.messages

    def to_agent_format(self):
        """Convert to the model expected structure"""
        return [
            {"role": m.role, "content": m.content}
            for m in self.messages
        ]
    

class LLMAgent():

    def __init__(self):
        
        self.agent = create_agent(
            "gpt-4.1",
            tools=[],
            # middleware=[
            #     rag_context_middleware,
            # ],
            checkpointer=InMemorySaver(),
        )

        self.turn_id = 0
        self.current_history: Optional[History] = None
        self.total_histories: Dict[int, History] = {}
        self.token_limit = 128000
        self.THRESHOLD = 0.001
        # 初始化第一个对话
        self.start_new_turn()

    def change_to_turn(self, id: int):
        if id in self.total_histories:
            self.turn_id = id
            self.current_history = self.total_histories[id]
            return True
        else:
            return False
        
        
    def start_new_turn(self):
        if self.current_history is not None:
            # 保存当前对话历史
            self.total_histories[self.turn_id] = self.current_history

        # 开始新的对话
        self.turn_id += 1
        self.current_history = History()
        self.total_histories[self.turn_id] = self.current_history

    def delete_turn(self, id: int):
        if id in self.total_histories:
            del self.total_histories[id]
            return True
        else:
            return False
    
    def show_all_turn_data(self):
        return self.total_histories

    def get_response(self, user_input: str) -> str:

        temp_message = Message(role="user", content=user_input, turn_id=self.turn_id)
        self.current_history.add(temp_message)

        try:
            agent_input = {
                "messages": self.current_history.to_agent_format(),
            }
            response = self.agent.invoke(agent_input,
                {
                    "configurable": {
                        "thread_id": str(self.turn_id),
                    }
                }
            )
        except Exception as e:
            print(f"Error preparing agent input: {e}")
            self.current_history.messages.pop()  # Remove the last user message
            return "Sorry, there was an error processing your request."

        assistant_message = Message(role="assistant", content=response["messages"][-1].content, turn_id=self.turn_id)
        self.current_history.add(assistant_message)

        self.update_history_summary(self.turn_id, user_input) # 更新为最新的用户输入
        token_used = self._extract_token_usage(response)
        if token_used is not None:
            self.update_history_token_usage(self.turn_id, token_used)

        return response["messages"][-1].content
    
    def update_history_summary(self, turn_id: int, summary: str):
        if turn_id in self.total_histories:
            self.total_histories[turn_id].summary = summary

    def update_history_token_usage(self, turn_id: int, token_used: int):
        if turn_id in self.total_histories:
            self.total_histories[turn_id].token_used = token_used

    def _extract_token_usage(self, response: Dict[str, Any]) -> Optional[int]:
        """Safely extract token usage from LangChain response."""
        messages = response.get("messages")
        if not isinstance(messages, list):
            return None

        for message in reversed(messages):
            meta = getattr(message, "response_metadata", None)
            if isinstance(meta, dict):
                token_usage = meta.get("token_usage", {}).get("total_tokens")
                if token_usage is not None:
                    return token_usage

        usage = response.get("usage") or response.get("response_metadata", {})
        if isinstance(usage, dict):
            token_usage = usage.get("token_usage", {}).get("total_tokens")
            if token_usage is not None:
                return token_usage

        return None
