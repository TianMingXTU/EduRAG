from langchain_core.stores import InMemoryStore
from langchain_classic.retrievers import ParentDocumentRetriever
from pathlib import Path
from edurag.rag_qa.edu_document_loaders.doc_loader import DocLoader
from edurag.rag_qa.edu_document_loaders.pdf_loader import PdfLoader
from edurag.rag_qa.edu_document_loaders.md_loader import MarkdownLoader
from edurag.rag_qa.edu_document_loaders.txt_loader import TextLoader
from edurag.rag_qa.edu_text_splitter.parent_child_splitter import parent_child_splitter
from edurag.rag_qa.models.embedding import embedding
from edurag.rag_qa.vector_manage.milvus_store import MilvusVector
from edurag.base.logger import logger


class MilvusVector:
    MILVUS_URI = "./milvus_demo.db"
    COLLECTION_NAME = "langchain_milvus_demo"

    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self.loader = None
        self.emb = embedding()
        self.vec = MilvusVector()
        if self.file_path.suffix in (".pdf"):
            self.loader = PdfLoader()
        elif self.file_path.suffix in (".md"):
            self.loader = MarkdownLoader()
        elif self.file_path.suffix in (".txt"):
            self.loader = TextLoader()
        elif self.file_path.suffix in (".doc", "docx"):
            self.loader = DocLoader()
        else:
            logger.error("传入错误的文档类型")
        self.retriever = self.create_retriever()

    def create_retriever(self):
        parent_splitter, child_splitter = parent_child_splitter()
        store = InMemoryStore()

        retriever = ParentDocumentRetriever(
            vectorstore=self.vec,
            docstore=store,
            child_splitter=child_splitter,
            parent_splitter=parent_splitter,
        )
        return retriever

    def store(self):
        documents = self.loader.load(self.file_path)
        self.retriever.add_documents(documents)

    def query(self, key):
        return self.retriever.invoke(key)
