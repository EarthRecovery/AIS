
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
        self.token_used = 0
        self.token_limit = 128000
        self.THRESHOLD = 0.001
        
        
    def start_new_turn(self):

        self.turn_id += 1
        self.current_history = History()
        self.total_histories[self.turn_id] = self.current_history
        self.token_used = 0
        self.current_history.token_used = self.token_used

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
        self.token_used = response['messages'][1].response_metadata['token_usage']['total_tokens'] # 获取总的 token 使用量，默认为当前值
        self.current_history.token_used = self.token_used

        return response["messages"][-1].content