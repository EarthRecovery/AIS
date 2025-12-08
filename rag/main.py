import os
from dotenv import load_dotenv
from rag.indexing.pipeline import Indexing
from rag.models.openai import OpenAIModel
from rag.retriving.retriveAgent import RetrieveAgent

if __name__ == "__main__":
    load_dotenv()
    model = OpenAIModel()
    data = Indexing(model).url_index("https://lilianweng.github.io/posts/2023-06-23-agent/")
    agent = RetrieveAgent(model)
    query = "What is an AI agent?"
    result = agent.answer(query)
    print("Answer:", result["answer"])
    print("Context:", result["context"])