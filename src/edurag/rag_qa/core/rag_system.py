from edurag.base.logger import logger
from edurag.rag_qa.core.query_classifier import classify_query
from edurag.rag_qa.core.strategy_selector import select_strategy, optimize_query
from edurag.rag_qa.core.prompts import answer_synthesis_prompt
from edurag.rag_qa.core.document_processor import HybridProcessor
from edurag.agent.llm import get_llm
from langchain_core.output_parsers import StrOutputParser

_processor = HybridProcessor()


def _search(query: str) -> list:
    return _processor.query(query)


def process(query: str) -> dict:
    classification = classify_query(query)
    logger.info(f"Query classification: {classification}")

    if classification == "general_knowledge":
        llm = get_llm()
        answer = llm.invoke(query).content
        return {
            "answer": answer,
            "classification": "general_knowledge",
            "strategy": None,
            "sources": [],
        }

    strategy = select_strategy(query)
    logger.info(f"Strategy selected: {strategy}")

    optimized = optimize_query(query, strategy)
    logger.info(f"Optimized query: {optimized}")

    all_docs = []
    if isinstance(optimized, list):
        for sub_q in optimized:
            docs = _search(sub_q)
            all_docs.extend(docs)
    else:
        all_docs = _search(optimized)

    if not all_docs:
        llm = get_llm()
        answer = llm.invoke(query).content
        return {
            "answer": answer,
            "classification": "professional_consultation",
            "strategy": strategy,
            "sources": [],
        }

    context = "\n\n".join(f"[{i+1}] {d.page_content}" for i, d in enumerate(all_docs))

    chain = answer_synthesis_prompt | get_llm() | StrOutputParser()
    answer = chain.invoke({"context": context, "query": query})

    return {
        "answer": answer,
        "classification": "professional_consultation",
        "strategy": strategy,
        "sources": [d.page_content[:100] for d in all_docs[:3]],
    }
