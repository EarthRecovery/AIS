from langchain.agents.middleware import AgentState, before_model
from langchain_core.messages import SystemMessage

from app.agent.persona_prompt import PERSONA_PROMPT


@before_model
def persona_middleware(state: AgentState, runtime):
    """Inject persona system prompt before model call."""
    return {"messages": [SystemMessage(content=PERSONA_PROMPT)]}
