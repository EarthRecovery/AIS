

# DataStore 是一个用于将文档块存储到向量存储中的类。
class DataStore:
    def __init__(self, model):
        self.model = model
    
    def store(self,data):
        self.model.openai_vector_store_model.add_documents(data)
        print(f"Total documents stored: {len(data)}")
        return self.model.openai_vector_store_model