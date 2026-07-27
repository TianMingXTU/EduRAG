from typing import Optional
from langchain_milvus import Milvus, BM25BuiltInFunction
from langchain_core.embeddings import Embeddings
from edurag.config.settings import settings
from edurag.document.splitter import get_parent_splitter, get_child_splitter
from edurag.storage.mysql import mysql_client


def _get_embedding_function() -> Embeddings:
    from langchain_openai import OpenAIEmbeddings

    return OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.embedding_api_key,
        base_url=settings.embedding_base_url,
    )


class VectorStoreManager:
    _dense: Milvus | None = None
    _hybrid: Milvus | None = None

    @classmethod
    async def init(cls) -> None:
        await mysql_client.ensure()
        if cls._dense is None:
            cls._dense = Milvus(
                embedding_function=_get_embedding_function(),
                connection_args={"uri": settings.MILVUS_DB_PATH},
                collection_name=settings.milvus_collection,
                drop_old=False,
                auto_id=True,
            )
        if cls._hybrid is None and settings.milvus_collection_hybrid:
            cls._hybrid = Milvus(
                embedding_function=_get_embedding_function(),
                builtin_function=BM25BuiltInFunction(),
                connection_args={"uri": settings.MILVUS_DB_PATH},
                collection_name=settings.milvus_collection_hybrid,
                drop_old=False,
                auto_id=True,
            )

    @classmethod
    def get_dense(cls) -> Milvus:
        if cls._dense is None:
            raise RuntimeError("VectorStoreManager not initialized — call init() first")
        return cls._dense

    @classmethod
    def get_hybrid(cls) -> Milvus | None:
        if cls._hybrid is None:
            raise RuntimeError("VectorStoreManager not initialized — call init() first")
        return cls._hybrid

    @classmethod
    async def close(cls) -> None:
        cls._dense = None
        cls._hybrid = None


milvus_store = VectorStoreManager()
