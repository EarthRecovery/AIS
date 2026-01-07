from langchain.agents.middleware import AgentState, before_model
from langchain_core.messages import SystemMessage

from app.agent.base_prompt import BASE_PROMPT


@before_model
def base_prompt_middleware(state: AgentState, runtime):

    message = SystemMessage(content=BASE_PROMPT)
    return message

def base_prompt_run() -> SystemMessage:
    message = SystemMessage(content=BASE_PROMPT)
    return message
