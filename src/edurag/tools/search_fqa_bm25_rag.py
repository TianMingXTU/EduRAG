from langchain.tools import tool
from edurag.mysql_qa.retrieval.bm25_search import BM25Search

_bm25_search = BM25Search()


def _ensure_index():
    import asyncio

    if _bm25_search.bm25 is None:
        asyncio.run(_bm25_search.build_index())


@tool
def search_fqa_bm25_rag(
    query: str,
) -> str | tuple[str | None, str | None, float | None]:
    """Searches the FAQ knowledge base using hybrid BM25 and RAG retrieval.

    This tool retrieves relevant frequently asked questions (FAQs) by combining
    BM25 keyword matching with RAG semantic search. Use this tool when users
    ask about general platform policies, course schedules, or need to look up
    exact technical terms and error codes.

    Args:
        query: A string containing search keywords or a natural language question.
            Example: "How to reset password" or "Python course schedule".

    Returns:
        A string containing the matched FAQ entries, or an error/status message
        if the search fails or yields no results.
    """
    try:
        _ensure_index()
        cleaned_query = query.strip()
        if not cleaned_query:
            return (
                "[Search Error]: The search query cannot be empty. "
                "Please provide valid keywords or a question."
            )

        result = _bm25_search.query(cleaned_query)

        return result

    except Exception as e:
        return (
            f"[System Error]: Failed to search the knowledge base. "
            f"Error details: {str(e)}. Please contact support if the issue persists."
        )
