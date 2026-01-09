# app/agent/middleware/rag_context.py
from tokenize import String
from langchain.agents.middleware import AgentState, before_model
from app.rag.models.openai import OpenAIModel
from langchain_core.messages import SystemMessage

_rag_model = OpenAIModel()


def _get_msg_role(msg):
    if isinstance(msg, dict):
        return msg.get("role")
    # LangChain messages expose `type`; fallback to `role` if present
    return getattr(msg, "type", None) or getattr(msg, "role", None)


@before_model
def rag_context_middleware(state: AgentState, runtime):
    role_settings = state.get("role_settings") if isinstance(state, dict) else None
    role_rag_name = getattr(role_settings, "rag_name", None) if role_settings else None
    messages = state["messages"]
    last_user = next((m for m in reversed(messages) if _get_msg_role(m) in ("human", "user")), None)
    if not last_user:
        return None
    if not role_rag_name:
        return None
    last_content = getattr(last_user, "content", None) if not isinstance(last_user, dict) else last_user.get("content")
    if last_content is None:
        return None
    docs = get_rag_docs(last_content, k=3, role_rag_name=role_rag_name)
    if not docs:
        return None
    ctx = "\n\n".join(d.page_content for d in docs)
    # print("[LLM][middleware][rag_context]", ctx)
    return {"messages": [SystemMessage(content=f"Use the retrieved context:\n{ctx}")]}

def rag_run(messages: list, role_rag_name=None) -> str:
    last_user = next((m for m in reversed(messages) if _get_msg_role(m) in ("human", "user")), None)
    if not last_user:
        return None
    last_content = getattr(last_user, "content", None) if not isinstance(last_user, dict) else last_user.get("content")
    if last_content is None or not role_rag_name:
        return None
    docs = get_rag_docs(last_content, k=10, role_rag_name=role_rag_name)
    # print(role_rag_name)
    # print(">>> RAG docs found:", len(docs))
    if not docs:
        return None
    ctx = "\n\n".join(d.page_content for d in docs)
    return ctx

def get_rag_docs(content, k, role_rag_name) -> list:
    vector_store = _rag_model.get_openai_vector_store_model(
        embedding_model=_rag_model.get_openai_embedding_model(),
        collection_name=role_rag_name,
    )
    docs = vector_store.similarity_search(content, k=k)
    return docs
