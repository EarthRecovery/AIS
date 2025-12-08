from langchain_community.document_loaders import WebBaseLoader
from bs4 import BeautifulSoup
import requests

# DocumentLoader 是一个用于从指定 URL 加载网页内容的类，提取其中的文本段落并返回为文档列表。
class DocumentLoader:

    def __init__(self, url: str):
        self.url = url

    # 从指定 URL 加载网页内容，提取所有段落文本并返回文档列表。
    def load_from_url(self):
        html = requests.get(self.url).text

        soup = BeautifulSoup(html, 'html.parser')
        p_tags = soup.find_all('p')
        page_text = "\n".join([tag.get_text() for tag in p_tags])
        docs = [{"page_content": page_text }]
        print(f"Total characters: {len(docs[0]['page_content'])}")
        print(f"Sample content: {docs[0]['page_content'][:500]}...")
        return docs