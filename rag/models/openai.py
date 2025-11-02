from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain.vectorstores import InMemoryVectorStore

class OpenAIModel:
    def __init__(self):
        self.openai_chat_model = self.get_openai_model()
        self.openai_embedding_model = self.get_openai_embedding_model()
        self.openai_vector_store_model = self.get_openai_vector_store_model(self.openai_embedding_model)

    def get_openai_model(self,model_name: str = "gpt-4.1"):
        if self.openai_chat_model is None:
            self.openai_chat_model = ChatOpenAI(model_name=model_name, temperature=0)
        return self.openai_chat_model

    def get_openai_embedding_model(self, model_name: str = "text-embedding-3-large"):
        if self.openai_embedding_model is None:
            self.openai_embedding_model = OpenAIEmbeddings(model_name=model_name)
        return self.openai_embedding_model

    def get_openai_vector_store_model(self, embedding_model: OpenAIEmbeddings):
        if self.openai_vector_store_model is None:
            self.openai_vector_store_model = InMemoryVectorStore(embedding=embedding_model)
        return self.openai_vector_store_model