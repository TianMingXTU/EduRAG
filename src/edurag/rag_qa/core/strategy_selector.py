from langchain_core.output_parsers import StrOutputParser
from edurag.agent.llm import get_llm
from edurag.rag_qa.core.prompts import (
    strategy_selector_prompt,
    hyde_prompt,
    subquery_prompt,
    backtrack_prompt,
)


def select_strategy(query: str) -> str:
    chain = strategy_selector_prompt | get_llm() | StrOutputParser()
    result = chain.invoke({"query": query})
    result = result.strip().lower()
    if result not in ("direct", "hyde", "subquery", "backtrack"):
        return "direct"
    return result


def optimize_query(query: str, strategy: str) -> str | list[str]:
    llm = get_llm()

    if strategy == "direct":
        return query

    if strategy == "hyde":
        chain = hyde_prompt | llm | StrOutputParser()
        return chain.invoke({"query": query})

    if strategy == "subquery":
        chain = subquery_prompt | llm | StrOutputParser()
        result = chain.invoke({"query": query})
        return [q.strip() for q in result.strip().split("\n") if q.strip()]

    if strategy == "backtrack":
        chain = backtrack_prompt | llm | StrOutputParser()
        return chain.invoke({"query": query})

    return query
