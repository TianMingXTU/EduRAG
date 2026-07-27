from edurag.document.processor import retrieve, ChunkStrategy
from edurag.agent.orchestrator import run_agent
from edurag.config.logging import logger


async def process(query: str) -> dict:
    result = await run_agent(query, max_iterations=3)
    return {
        "answer": result["answer"],
        "confidence": result["confidence"],
        "strategy": result["strategy"],
        "sources": result["sources"],
        "iterations": result["iterations"],
    }


async def retrieve_only(query: str, k: int = 5) -> list:
    docs = await retrieve(query, strategy=ChunkStrategy.HYBRID, k=k)
    return [
        {"content": d.page_content, "source": d.metadata.get("source", "unknown")}
        for d in docs
    ]
