from edurag.config.settings import settings
from httpx import Client
from langchain_core.documents import Document


class SiliconFlowRerank:
    def __init__(
        self,
        model: str,
        api_key: str,
        top_n: int = 3,
        base_url: str | None = None,
    ):
        self.model = model
        self.api_key = api_key
        self.top_n = top_n
        self.base_url = base_url or "https://api.siliconflow.cn/v1/rerank"

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

    def __call__(self, documents, query, callbacks=None) -> list[Document]:
        return self.compress_documents(documents, query, callbacks)


def rerank():
    return SiliconFlowRerank(
        model=settings.rerank_model,
        api_key=settings.rerank_api_key,
        top_n=3,
    )
