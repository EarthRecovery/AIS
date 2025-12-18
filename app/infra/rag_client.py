
from app.rag.app import RagApp


class RAGClient:
    def __init__(self):
        self.app = RagApp()

    def add_context(self, context: str, channel: str = "default"):
        return self.app.add_context(context, channel)
    
    def is_active(self):
        return self.app.get_active_status()
    
    def clear_collection(self, collection_name: str):
        return self.app.clear_collection(collection_name)
    
    def get_vector_line_count(self, collection_name: str):
        return self.app.get_vector_line_count(collection_name)  
    
    def get_collection_names(self):
        return self.app.get_collection_names()

