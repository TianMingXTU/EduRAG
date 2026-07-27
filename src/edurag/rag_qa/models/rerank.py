from edurag.base.config import config
from httpx import Client
from langchain_core.documents import Document
from langchain_classic.retrievers.document_compressors.base import (
    BaseDocumentCompressor,
)


class SiliconFlowRerank(BaseDocumentCompressor):
    model: str
    api_key: str
    top_n: int = 3
    base_url: str = config.rerank_base_url or "https://api.siliconflow.cn/v1/rerank"

    def compress_documents(self, documents, query, callbacks=None) -> list[Document]:
        docs_text = [d.page_content for d in documents]
        resp = Client(headers={"Authorization": f"Bearer {self.api_key}"}).post(
            self.base_url,
            json={
                "model": self.model,
                "query": query,
                "documents": docs_text,
                "top_n": self.top_n,
            },
            timeout=60,
        )
        resp.raise_for_status()
        indices = [r["index"] for r in resp.json()["results"]]
        return [documents[i] for i in indices]


def rerank():
    return SiliconFlowRerank(
        model=config.rerank_model,
        api_key=config.rerank_api_key,
        top_n=3,
    )
