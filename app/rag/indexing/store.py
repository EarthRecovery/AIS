# DataStore 是一个用于将文档块存储到向量存储中的类。
class DataStore:
    def __init__(self, model):
        self.model = model
    
    def store(self,data, collection_name: str = "default_collection"):
        self.model.get_openai_vector_store_model(embedding_model=self.model.get_openai_embedding_model(), collection_name=collection_name).add_vectors(data)