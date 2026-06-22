from functools import lru_cache

from core.clients.llm_client import LLMClient
from core.clients.rag_client import RAGClient


@lru_cache()
def get_llm_client():
    return LLMClient()

@lru_cache()
def get_rag_client():
    return RAGClient()

@lru_cache()
def get_chat_service():
    from modules.chat.service import ChatService
    return ChatService()