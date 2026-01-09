import json
from pathlib import Path
from app.rag.indexing.pipeline import Indexing
from app.rag.indexing.splitter import DataSplitter
from app.rag.models.openai import OpenAIModel
from app.rag.models.vectorStore import VectorStore
import chromadb

class RagApp:
    def __init__(self):
        self.is_active = True
        self.model =  OpenAIModel()
        self.persist_dir = "./data/chroma_db"

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
        return True

    def delete_collection(self, collection_name: str):
        # Alias for clarity; currently same implementation as clear_collection
        return self.clear_collection(collection_name)

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
    
    def create_collection_from_json_list_file(self, json_list_file: str, collection_name: str, skip_split: bool = False) -> int:
        self.deactivate()
        try:
            json_path = Path(json_list_file)
            if not json_path.exists():
                raise FileNotFoundError(f"JSON file not found: {json_path}")

            with json_path.open("r", encoding="utf-8") as file:
                data = json.load(file)

            if not isinstance(data, list) or not all(isinstance(item, str) for item in data):
                raise ValueError("JSON file must contain a list of strings.")

            docs = [
                {"page_content": item.strip(), "metadata": {"source": json_path.name, "index": idx}}
                for idx, item in enumerate(data)
                if isinstance(item, str) and item.strip()
            ]
            if not docs:
                return 0

            # chunks = DataSplitter().split(docs)
            chunks = docs if skip_split else DataSplitter().split(docs)
            vector_store = VectorStore(
                self.model.get_openai_embedding_model(),
                collection_name=collection_name,
                persist_directory=self.persist_dir,
            )
            vector_store.add_vectors(chunks, jump_duplicate=False)
            return len(chunks)
        finally:
            self.activate()
