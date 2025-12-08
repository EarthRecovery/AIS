from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from rag.models.openai import OpenAIModel
from langgraph.checkpoint.memory import InMemorySaver

#Agent 是一个检索增强生成（RAG）系统的组件，负责从向量存储中检索相关文档，并基于这些文档生成回答。
class RetrieveAgent:
    def __init__(self, model: OpenAIModel):
        self.model = model

    # 使用向量存储模型检索与查询最相关的文档。k 指定要检索的文档数量。
    def retrieve(self, query: str, k: int = 3):
        retriever = self.model.openai_vector_store_model.as_retriever(search_type="similarity", search_kwargs={"k": k})
        docs = retriever.invoke(query)
        return docs

    # 输入查询，检索相关文档，并基于这些文档生成回答。
    def answer(self,query: str):
        docs = self.retrieve(query)
        context = "\n\n".join([f"Source: {d.metadata.get('source', 'N/A')}\n{d.page_content}" for d in docs])

        system_prompt = """You are a knowledgeable assistant that answers questions using the provided context. If the answer is not in the context, say you don't know."""
        template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "Context:\n{context}\n\nQuestion: {question}")
        ])
        prompt = template.format(context=context, question=query)

        llm = self.model.openai_chat_model
        response = llm.invoke(prompt)

        return {
            "answer": response.content,
            "context": context
        }