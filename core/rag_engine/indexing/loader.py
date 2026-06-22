
from readability import Document
from langchain_community.document_loaders import WebBaseLoader
from bs4 import BeautifulSoup
from bs4.element import TemplateString
import trafilatura
import requests

# DocumentLoader 是一个用于从指定 URL 加载网页内容的类，提取其中的文本段落并返回为文档列表。
class DocumentLoader:

    def __init__(self):
        pass

    # 从指定 URL 加载网页内容，提取所有段落文本并返回文档列表。
    def load_from_url(self, url: str = None):
        pass
    
    def web_loader(self):
        pass

    def load_from_channel(self, context: str, channel: str):
        if channel == "moegirl":
            return self.load_from_moegirl(context)
    
    def load_from_moegirl(self, title: str = None):
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        params = {
            "action": "parse",
            "page": title,
            "prop": "text",
            "format": "json"
        }
        r = requests.get(
            "https://zh.moegirl.org.cn/api.php",
            params=params,
            headers=headers,
            timeout=10
        ).json()

        html = r["parse"]["text"]["*"]
        soup = BeautifulSoup(html, "html.parser")
        li_list = soup.find_all(["p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "br", "div"])
        texts = [li.get_text(strip=True) for li in li_list if li.get_text(strip=True)]
        jtext = "\n".join(texts)
        return [{"page_content": jtext, "metadata": {"source": title or self.url}}]
        # return soup.get_text(separator="\n", strip=True)