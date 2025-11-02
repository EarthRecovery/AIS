import os
from dotenv import load_dotenv
from rag.indexing.loader import DocumentLoader

if __name__ == "__main__":
    load_dotenv()
    docs = DocumentLoader("https://lilianweng.github.io/posts/2023-06-23-agent/").load_from_url()