from langchain_community.vectorstores import Chroma
from chromadb import PersistentClient
import hashlib
from langchain_core.documents import Document

class VectorStore:
    def __init__(self, embedding_model, collection_name: str = "default_collection", persist_directory: str | None = None):
        self.persist_dir = persist_directory or "./data/chroma_db"
        self.collection_name = collection_name
        self.store = Chroma(
            embedding_function=embedding_model,
            collection_name=collection_name,
            persist_directory=self.persist_dir
        )

        self.client = PersistentClient(path=self.persist_dir)

    def add_vectors(self, vectors, jump_duplicate=True):
        print(">>> add_vectors CALLED")
        print(">>> num vectors:", len(vectors))
        delete_rows = 0
        add_rows = 0
        
        for doc in vectors:
            if isinstance(doc, dict):
                doc = Document(
                    page_content=doc.get("page_content", ""),
                    metadata=doc.get("metadata", {}) or {},
                )
            doc.metadata["doc_id"] = self.doc_id(doc)
            # 去重
            if jump_duplicate:
                existing_docs = self.store.similarity_search(doc.page_content, k=1)
                if existing_docs:
                    if existing_docs[0].metadata.get("doc_id") == doc.metadata["doc_id"]:
                        delete_rows += 1
                        print(f">>> Duplicate document found, skipping: {doc.metadata.get('source', 'N/A')}")
                        continue
            self.store.add_documents([doc])
            print(f">>> Document added: {doc.page_content[:30]}...")
            add_rows += 1
            print(f">>> Documents added so far: {add_rows}")
        print(">>> add_vectors DONE")
        print(f">>> Vectors added: {len(vectors) - delete_rows}, Duplicates skipped: {delete_rows}")
        self.store.persist()
        print(">>> persist DONE")

    def doc_id(self, doc):
        return hashlib.sha256(
            doc.page_content.encode("utf-8")
        ).hexdigest()

    def similarity_search(self, query, k=3):
        return self.store.similarity_search(query, k=k)
    
    def clear_collection(self):
        try:
            self.client.delete_collection(self.collection_name)
        except Exception as e:
            print(f"Error getting collection: {e}")

    def get_collection_count(self):
        try:
            collection = self.client.get_collection(self.collection_name)
            return collection.count()
        except Exception as e:
            print(f"Error getting collection: {e}")
            return 0
        
