from app.infra.llm_client import LLMClient
from app.services.deps import get_llm_client, get_rag_client
from fastapi import Depends

class RagService:
    
    def __init__(self, rag: LLMClient = Depends(get_rag_client)):
        self.rag = rag

    def add_context(self, context: str, channel: str = "default"):
        return self.rag.add_context(context, channel)
    
    def is_service_available(self):
        return self.rag.is_active()
    
    async def clear_collection(self, collection_name: str):
        return self.rag.clear_collection(collection_name)
    
    async def get_vector_line_count(self, collection_name: str):
        return self.rag.get_vector_line_count(collection_name)
    
    async def get_collection_names(self):
        return self.rag.get_collection_names()