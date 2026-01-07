
from langchain.agents.middleware import AgentState, before_model
from langchain_core.messages import SystemMessage

from app.agent.role_prompt import load_role_prompt


@before_model
def role_prompt_middleware(state: AgentState, runtime):

    role_settings = state.get("role_settings") if isinstance(state, dict) else None
    prompt = load_role_prompt(role_settings)
    message = SystemMessage(content=prompt)
    return message