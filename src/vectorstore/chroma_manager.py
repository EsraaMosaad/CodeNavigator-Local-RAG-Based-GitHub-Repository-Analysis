import os
import re
import chromadb
from langchain_chroma import Chroma
from src.core.base import BaseVectorStore

class ChromaManager(BaseVectorStore):
    def __init__(self, base_path="vector_stores"):
        self.base_path = os.path.abspath(base_path)

    def _sanitize_name(self, name: str) -> str:
        clean_name = re.sub(r'[^a-zA-Z0-9]', '_', name).strip('_')
        if len(clean_name) < 3: clean_name = f"repo_{clean_name}"
        return clean_name

    def create_or_load(self, texts, repo_name: str, embedding_function) -> Chroma:
        clean_name = self._sanitize_name(repo_name)
        repo_db_path = os.path.join(self.base_path, clean_name)
        
        # Check if vector store already exists for this repo
        exists = os.path.exists(repo_db_path)
        
        if texts and not exists:
            os.makedirs(repo_db_path, exist_ok=True)
            client = chromadb.PersistentClient(path=repo_db_path)
            return Chroma.from_documents(
                documents=texts,
                embedding=embedding_function,
                client=client,
                collection_name=clean_name
            )
        elif exists:
            client = chromadb.PersistentClient(path=repo_db_path)
            return Chroma(
                client=client,
                embedding_function=embedding_function,
                collection_name=clean_name
            )
        return None
