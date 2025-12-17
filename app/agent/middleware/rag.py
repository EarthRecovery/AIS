# app/agent/middleware/rag_context.py
from langchain.agents.middleware import AgentState, before_model
from app.rag.models.openai import OpenAIModel
from langchain_core.messages import SystemMessage

_rag_model = OpenAIModel()
vector_store = _rag_model.get_openai_vector_store_model(
    embedding_model=_rag_model.get_openai_embedding_model(),
    collection_name="default_collection",
)

@before_model
def rag_context_middleware(state: AgentState, runtime):
    messages = state["messages"]
    last_user = next((m for m in reversed(messages) if m.type == "human"), None)
    if not last_user:
        return None
    docs = vector_store.similarity_search(last_user.content, k=3)
    if not docs:
        return None
    ctx = "\n\n".join(d.page_content for d in docs)
    return {"messages": [SystemMessage(content=f"Use the retrieved context:\n{ctx}")]}
