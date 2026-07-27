from typing import Any
from langchain.tools import tool
from edurag.rag_qa.core.rag_system import process


@tool
def search_knowledge_base(query: str) -> str:
    """Searches the enterprise knowledge base with automatic strategy selection.

    Analyzes the query, selects the best retrieval strategy (direct/hyde/subquery/backtrack),
    performs hybrid dense+sparse search, and synthesizes the final answer.
    """
    try:
        cleaned = query.strip()
        if not cleaned:
            return "Search query cannot be empty."
        result = process(cleaned)
        strategy_info = (
            f"[Strategy: {result['strategy']}] " if result["strategy"] else ""
        )
        return f"{strategy_info}{result['answer']}"
    except Exception as e:
        return f"Search failed: {str(e)}"
