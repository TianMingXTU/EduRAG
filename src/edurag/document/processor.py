from typing import Any
from enum import Enum
from pathlib import Path
import pickle

from langchain_core.documents import Document

from edurag.config.settings import settings
from edurag.document.loader import load_documents
from edurag.document.splitter import get_parent_splitter, get_child_splitter
from edurag.storage.vector import milvus_store


class ChunkStrategy(str, Enum):
    DENSE = "dense"
    HYBRID = "hybrid"


async def ingest(
    file_path: str | Path,
    strategy: ChunkStrategy = ChunkStrategy.DENSE,
) -> int:
    path = Path(file_path)
    documents = await load_documents(path)

    parent_splitter = get_parent_splitter()
    child_splitter = get_child_splitter()

    parent_chunks = parent_splitter.split_documents(documents)

    child_chunks: list[Document] = []
    for parent in parent_chunks:
        sub_chunks = child_splitter.split_documents([parent])
        child_chunks.extend(sub_chunks)

    collection = (
        milvus_store.get_hybrid()
        if strategy == ChunkStrategy.HYBRID
        else milvus_store.get_dense()
    )
    collection.add_documents(child_chunks)
    return len(child_chunks)


async def retrieve(
    query: str,
    strategy: ChunkStrategy = ChunkStrategy.DENSE,
    k: int = settings.retrieval_k,
) -> list[Document]:
    collection = (
        milvus_store.get_hybrid()
        if strategy == ChunkStrategy.HYBRID
        else milvus_store.get_dense()
    )
    results = collection.similarity_search(query, k=k)
    return results
