import os
import re
import shutil
import chromadb
from chromadb.config import Settings
from langchain_chroma import Chroma
from src.core.base import BaseVectorStore

class ChromaManager(BaseVectorStore):
    def __init__(self, base_path="vector_stores"):
        self.base_path = os.path.abspath(base_path)

    def _sanitize_name(self, name: str) -> str:
        clean_name = re.sub(r'[^a-zA-Z0-9]', '_', name).strip('_')
        if len(clean_name) < 3: clean_name = f"repo_{clean_name}"
        return clean_name

    def _fresh_client(self, path: str) -> chromadb.PersistentClient:
        """Always return a fresh PersistentClient, resetting any cached singleton state."""
        try:
            chromadb.api.client.SharedSystemClient.clear_system_cache()
        except Exception:
            pass
        os.makedirs(path, exist_ok=True)
        # allow_reset=True lets chromadb recover from a dirty/partial state
        settings = Settings(allow_reset=True, anonymized_telemetry=False)
        return chromadb.PersistentClient(path=path, settings=settings)

    def create_or_load(self, texts, repo_name: str, embedding_function) -> Chroma:
        clean_name = self._sanitize_name(repo_name)
        repo_db_path = os.path.join(self.base_path, clean_name)

        exists = os.path.exists(repo_db_path)

        if texts and not exists:
            client = self._fresh_client(repo_db_path)
            return Chroma.from_documents(
                documents=texts,
                embedding=embedding_function,
                client=client,
                collection_name=clean_name
            )
        elif exists:
            client = self._fresh_client(repo_db_path)
            return Chroma(
                client=client,
                embedding_function=embedding_function,
                collection_name=clean_name
            )
        return None
