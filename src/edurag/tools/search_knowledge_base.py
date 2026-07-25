from typing import Any

from edurag.rag_qa.core.document_processor import Processor
from langchain.tools import tool

_processor = Processor()


@tool
def search_knowledge_base(query: str) -> list[dict[str, Any]] | str:
    """Searches the enterprise knowledge base for relevant documents based on a query.

    This tool performs dense vector similarity search (and parent-child chunking)
    against the configured knowledge base. Use this tool whenever you need to
    retrieve domain-specific facts, architecture specs, or corporate policies.

    Args:
        query (str): The search query or keywords. Should be a high-density,
            specific semantic query (e.g., "Nacos configuration refresh steps").

    Returns:
        list[dict[str, Any]] | str: A list of retrieved document objects containing
        page contents and metadata, or a text summary of search results.

    Raises:
        RuntimeError: If an error occurs during the document processor query execution.
    """
    try:
        cleaned_query = query.strip()
        if not cleaned_query:
            return "Search query cannot be empty."

        result = _processor.query(cleaned_query)
        return result

    except Exception as e:
        return f"Failed to search knowledge base due to error: {str(e)}"
