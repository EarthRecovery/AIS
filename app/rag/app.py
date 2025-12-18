from app.rag.indexing.pipeline import Indexing
from app.rag.models.openai import OpenAIModel
import chromadb

class RagApp:
    def __init__(self):
        self.is_active = True
        self.model =  OpenAIModel()
        self.persist_dir = "/home/kaslana/AIS/data/chroma_db"

    def deactivate(self):
        self.is_active = False

    def activate(self):
        self.is_active = True

    def get_active_status(self):
        return self.is_active
    
    def add_context(self, context: str, channel: str = "default"):
        # Here you would add the context to your RAG system
        self.deactivate()
        try:
            data = Indexing(self.model).channel_index(context, channel, collection_name="default_collection")
        except Exception as e:
            print(f"Error adding context: {e}")
            data = None
        finally:
            self.activate()
        return data
    
    def clear_collection(self, collection_name: str):
        vector_store = self.model.get_openai_vector_store_model(
            embedding_model=self.model.get_openai_embedding_model(),
            collection_name=collection_name,
            persist_directory=self.persist_dir,
        )
        vector_store.clear_collection()

    def get_vector_line_count(self, collection_name: str):
        print(collection_name)
        vector_store = self.model.get_openai_vector_store_model(
            embedding_model=self.model.get_openai_embedding_model(),
            collection_name=collection_name,
            persist_directory=self.persist_dir,
        )
        return vector_store.get_collection_count()
    
    def get_collection_names(self):
        client = chromadb.PersistentClient(path=self.persist_dir)
        collections = client.list_collections()
        collection_names = [col.name for col in collections]
        return collection_names
        
    
