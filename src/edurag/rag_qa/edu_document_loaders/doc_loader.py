from pathlib import Path
from langchain_community.document_loaders import Docx2txtLoader
from edurag.rag_qa.edu_document_loaders.base_loader import BaseLoader


class DocLoader(BaseLoader):
    def load(self, file_path):
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Doc 文件未找到: {file_path}")
        loader = Docx2txtLoader(str(file_path))

        documents = loader.load()

        return documents
