from langchain_huggingface import HuggingFaceEmbeddings
from src.core.base import BaseEmbeddings

class HFEmbeddings(BaseEmbeddings):
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name

    def get_embedding_function(self):
        return HuggingFaceEmbeddings(model_name=self.model_name)
