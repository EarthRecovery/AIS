
from langchain.agents import create_agent, AgentState
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables import RunnableConfig
from langchain.agents.middleware import SummarizationMiddleware
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
        load_dotenv()
        self.agent = create_agent(
            "gpt-4.1",
            tools=[],
            middleware=[SummarizationMiddleware(
                model="gpt-4o-mini",
                # trigger=("tokens", 4000),
                # keep=("messages", 20),
            ),
        ],
            checkpointer=InMemorySaver(),
        )

        self.turn_id = 0
        self.history = History()
        self.total_histories: Dict[int, History] = {}
        self.token_limit = 128000
        self.THRESHOLD = 0.001
        
        
    def start_new_turn(self):

        self.total_histories[self.turn_id] = self.history # 保存当前对话历史

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

        token_usage = self._extract_token_usage(response)
        if token_usage is not None:
            self.current_history.token_used = token_usage
            self.total_histories[self.turn_id] = self.current_history

        return response["messages"][-1].content

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
