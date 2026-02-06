from typing import List, Any
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import LanguageParser
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter
from src.core.base import BaseParser

class PythonParser(BaseParser):
    def __init__(self, chunk_size=1000, chunk_overlap=100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def parse_and_split(self, path: str) -> List[Any]:
        loader = GenericLoader.from_filesystem(
            path,
            glob="**/*.py",
            suffixes=[".py"],
            parser=LanguageParser(language=Language.PYTHON)
        )
        documents = loader.load()
        
        if not documents:
            return []
            
        python_splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.PYTHON, 
            chunk_size=self.chunk_size, 
            chunk_overlap=self.chunk_overlap
        )
        return python_splitter.split_documents(documents)
