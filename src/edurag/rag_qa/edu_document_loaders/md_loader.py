from pathlib import Path
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from edurag.rag_qa.edu_document_loaders.base_loader import BaseLoader


class MarkdownLoader(BaseLoader):
    def load(self, file_path):
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Md 文件未找到: {file_path}")
        loader = UnstructuredMarkdownLoader(str(file_path))

        documents = loader.load()

        return documents
