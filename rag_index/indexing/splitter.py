from langchain_text_splitters import RecursiveCharacterTextSplitter

# DataSplitter 是一个用于将文本数据拆分为更小块的类，便于后续处理和存储。
class DataSplitter:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    def split(self, text):
        raw_texts = [doc["page_content"] for doc in text]
        chunks = self.splitter.create_documents(raw_texts)
        return chunks
    
