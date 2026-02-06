from abc import ABC, abstractmethod
from typing import List, Any

class BaseLoader(ABC):
    @abstractmethod
    def load(self, repo_url: str, target_path: str) -> str:
        pass

class BaseParser(ABC):
    @abstractmethod
    def parse_and_split(self, path: str) -> List[Any]:
        pass

class BaseEmbeddings(ABC):
    @abstractmethod
    def get_embedding_function(self):
        pass

class BaseVectorStore(ABC):
    @abstractmethod
    def create_or_load(self, texts: List[Any], repo_name: str, embedding_function: Any) -> Any:
        pass

class BaseInferenceModel(ABC):
    @abstractmethod
    def get_llm(self) -> Any:
        pass
