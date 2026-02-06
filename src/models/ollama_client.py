from langchain_community.llms import Ollama
from src.core.base import BaseInferenceModel

class OllamaModel(BaseInferenceModel):
    def __init__(self, model_name="deepseek-coder-v2:lite"):
        self.model_name = model_name

    def get_llm(self):
        return Ollama(model=self.model_name)
