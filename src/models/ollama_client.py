from langchain_ollama import OllamaLLM
from src.core.base import BaseInferenceModel

class OllamaModel(BaseInferenceModel):
    def __init__(self, model_name="deepseek-coder-v2:lite"):
        self.model_name = model_name

    def get_llm(self, **kwargs):
        return OllamaLLM(model=self.model_name, **kwargs)
