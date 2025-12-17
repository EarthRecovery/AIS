from app.rag.indexing.loader import DocumentLoader
from app.rag.indexing.splitter import DataSplitter
from app.rag.indexing.store import DataStore

# Indexing 是一个用于处理文档索引的类，负责从 URL 加载文档、拆分文档并将其存储到向量存储中。
class Indexing:
    def __init__(self, model):
        self.model = model

    # 从指定的 URL 加载文档，拆分文档为更小的块，并将这些块存储到向量存储中。
    # pipeline
    def url_index(self, url: str, ):
        docs = DocumentLoader(url).load_from_url() # 从指定 URL 加载网页内容，提取所有段落文本并返回文档列表。
        chunks = DataSplitter().split(docs) # 将文档拆分为更小的块，便于后续处理和存储。
        DataStore(self.model).store(chunks, collection_name="default_collection") # 将拆分后的文档块存储到向量存储中。
