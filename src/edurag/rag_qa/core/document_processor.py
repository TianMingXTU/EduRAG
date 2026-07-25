import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
from langchain_community.storage import RedisStore
from langchain_classic.storage import EncoderBackedStore
from langchain_classic.retrievers import ParentDocumentRetriever
from pathlib import Path
from redis import Redis
import pickle
from edurag.rag_qa.edu_document_loaders.doc_loader import DocLoader
from edurag.rag_qa.edu_document_loaders.pdf_loader import PdfLoader
from edurag.rag_qa.edu_document_loaders.md_loader import MarkdownLoader
from edurag.rag_qa.edu_document_loaders.txt_loader import TxtLoader
from edurag.rag_qa.edu_text_splitter.parent_child_splitter import parent_child_splitter
from edurag.rag_qa.models.embedding import embedding
from edurag.rag_qa.vector_manage.milvus_store import get_milvus
from edurag.base.logger import logger


class Processor:
    MILVUS_URI = "./milvus_demo.db"
    COLLECTION_NAME = "langchain_milvus_demo"

    def __init__(self):
        self.loader = None
        self.redis = Redis.from_url(url="redis://localhost:6379")
        self.emb = embedding()
        self.vec = get_milvus()
        self.retriever = self.create_retriever()

    def create_retriever(self):
        parent_splitter, child_splitter = parent_child_splitter()

        ubderlying_redis_store = RedisStore(client=self.redis, namespace="parent_docs")

        store = EncoderBackedStore(
            store=ubderlying_redis_store,
            key_encoder=lambda k: k,
            value_serializer=pickle.dumps,
            value_deserializer=pickle.loads,
        )

        retriever = ParentDocumentRetriever(
            vectorstore=self.vec,
            docstore=store,
            child_splitter=child_splitter,
            parent_splitter=parent_splitter,
            search_kwargs={"k": 5},
        )
        return retriever

    def store(self, file_path):
        file_path = Path(file_path)
        if file_path.suffix in (".pdf"):
            self.loader = PdfLoader()
        elif file_path.suffix in (".md"):
            self.loader = MarkdownLoader()
        elif file_path.suffix in (".txt"):
            self.loader = TxtLoader()
        elif file_path.suffix in (".doc", ".docx"):
            self.loader = DocLoader()
        else:
            logger.error("传入错误的文档类型")
        documents = self.loader.load(file_path)
        self.retriever.add_documents(documents)
        logger.info("加载文档成功")

    def query(self, key):
        logger.info(f"正在查询{key}")
        return self.retriever.invoke(key)


if __name__ == "__main__":
    processor = Processor()
    processor.store(file_path="plan.md")
    result = processor.query("EduRAG项目背景是什么?")
    print(f"个数:{len(result)}")
    print(f"{result[-1]}")
