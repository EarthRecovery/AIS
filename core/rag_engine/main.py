import os
from dotenv import load_dotenv
from indexing.pipeline import Indexing
from models.openai import OpenAIModel
from retriving.retriveAgent import RetrieveAgent

if __name__ == "__main__":
    load_dotenv()
    model = OpenAIModel()
    data = Indexing(model).url_index("https://zh.moegirl.org.cn/%E7%88%B1%E5%9F%8E%E5%8D%8E%E6%81%8B")
