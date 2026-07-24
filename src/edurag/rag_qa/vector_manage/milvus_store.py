from langchain_milvus import Milvus
from edurag.rag_qa.models.embedding import embedding

MILVUS_URI = "./milvus_demo.db"
COLLECTION_NAME = "langchain_milvus_demo"


def MilvusVector():
    return Milvus(
        embedding_function=embedding(),
        connection_args={"uri": MILVUS_URI},
        collection_name=COLLECTION_NAME,
        drop_old=True,
        auto_id=True,
    )
