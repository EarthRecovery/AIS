from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import InMemoryVectorStore
from langchain_anthropic import ChatAnthropic
from models.vectorStore import VectorStore

# OpenAIModel 是一个封装了 OpenAI 相关模型的类，提供聊天模型、嵌入模型和向量存储模型的初始化和访问方法。
# openai_model: 聊天生成模型，用于处理对话和生成文本响应。
# openai_embedding_model: 嵌入模型，用于将文本转换为向量
# openai_vector_store_model: 向量存储模型，用于存储和检索向量化的文档。
class OpenAIModel:
    def __init__(self):
        self.openai_chat_model = None
        self.openai_embedding_model = None
        self.openai_vector_store_model = None

        self.openai_chat_model = self.get_openai_model()
        self.openai_embedding_model = self.get_openai_embedding_model()
        self.openai_vector_store_model = self.get_openai_vector_store_model(self.openai_embedding_model, collection_name="default_collection")

    def get_openai_model(self,model: str = "gpt-4.1"):
        if self.openai_chat_model is None:
            self.openai_chat_model = ChatOpenAI(model=model, temperature=0)
        return self.openai_chat_model
    
    def get_anthropic_model(self, model: str = "claude-3-5-sonnet-20241022"):
        if self.anthropic_chat_model is None:
            self.anthropic_chat_model = ChatAnthropic(model=model, temperature=0)
        return self.anthropic_chat_model

    def get_openai_embedding_model(self, model: str = "text-embedding-3-large"):
        if self.openai_embedding_model is None:
            self.openai_embedding_model = OpenAIEmbeddings(model=model)
        return self.openai_embedding_model

    def get_openai_vector_store_model(self, embedding_model: OpenAIEmbeddings, collection_name: str = "default_collection"):
        if self.openai_vector_store_model is None:
            self.openai_vector_store_model = VectorStore(embedding_model, collection_name=collection_name)
        return self.openai_vector_store_model
