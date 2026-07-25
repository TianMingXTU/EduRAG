from langchain_milvus import Milvus, BM25BuiltInFunction
from edurag.rag_qa.models.embedding import embedding

MILVUS_URI = "./milvus_demo.db"
COLLECTION_NAME = "langchain_milvus_demo"
COLLECTION_NAME_HY = "langchain_hy_milvus_demo"


def get_milvus():
    return Milvus(
        embedding_function=embedding(),
        connection_args={"uri": MILVUS_URI},
        collection_name=COLLECTION_NAME,
        drop_old=False,
        auto_id=True,
    )


def get_hybrid_milvus():
    return Milvus(
        embedding_function=embedding(),
        builtin_function=BM25BuiltInFunction(),
        connection_args={"uri": MILVUS_URI},
        collection_name=COLLECTION_NAME_HY,
        drop_old=False,
        auto_id=True,
    )
