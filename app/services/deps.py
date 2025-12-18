from functools import lru_cache

from app.infra.llm_client import LLMClient
from app.infra.rag_client import RAGClient


@lru_cache()
def get_llm_client():
    return LLMClient()

@lru_cache()
def get_rag_client():
    return RAGClient()
