from langchain_community.vectorstores import Chroma
import hashlib

class VectorStore:
    def __init__(self, embedding_model, collection_name: str = "default_collection"):
        self.store = Chroma(
            embedding_function=embedding_model,
            collection_name=collection_name,
            persist_directory="/home/kaslana/AIS/data/chroma_db"
        )

    def add_vectors(self, vectors):
        print(">>> add_vectors CALLED")
        print(">>> num vectors:", len(vectors))
        for doc in vectors:
            doc.metadata["doc_id"] = self.doc_id(doc)
            # 去重
            existing_docs = self.store.similarity_search(doc.page_content, k=1)
            if existing_docs:
                if existing_docs[0].metadata.get("doc_id") == doc.metadata["doc_id"]:
                    print(f">>> Duplicate document found, skipping: {doc.metadata.get('source', 'N/A')}")
                    continue
            self.store.add_documents([doc])
        print(">>> add_vectors DONE")
        self.store.persist()
        print(">>> persist DONE")

    def doc_id(self, doc):
        return hashlib.sha256(
            doc.page_content.encode("utf-8")
        ).hexdigest()

    def similarity_search(self, query, k=3):
        return self.store.similarity_search(query, k=k)