import json
from typing import Any
from langchain_core.documents import Document
from edurag.config.settings import settings
from edurag.config.logging import logger
from edurag.document.processor import retrieve, ChunkStrategy
from edurag.prompt.templates import (
    PLAN_PROMPT,
    EVALUATE_PROMPT,
    SELF_CRITIQUE_PROMPT,
    SYNTHESIZE_PROMPT,
    HUMAN_ESCALATION_PROMPT,
)
from edurag.storage.redis import RedisManager


async def plan_node(state: dict) -> dict:
    llm = _get_llm()
    chain = PLAN_PROMPT | llm | _output_parser()
    result = chain.invoke({"query": state["query"], "iteration": state["iteration"]})

    query_type = result.get("query_type", "professional_consultation")
    strategy = result.get("strategy", "direct")
    sub_queries = result.get("sub_queries", [state["query"]])

    return {
        **state,
        "query_type": query_type,
        "strategy": strategy,
        "sub_queries": sub_queries if isinstance(sub_queries, list) else [sub_queries],
        "iteration": state.get("iteration", 0) + 1,
    }


async def fqa_lookup_node(state: dict) -> dict:
    query = state["query"]

    cached = await RedisManager.get_fqa(query)
    if cached:
        data = json.loads(cached) if isinstance(cached, str) else cached
        logger.info(f"FQA cache hit for: {query[:40]}")
        return {
            **state,
            "synthesis_answer": data["answer"],
            "confidence": 1.0,
            "source_references": ["FQA database (cached)"],
        }

    try:
        from edurag.storage.mysql import DatabaseManager
        from edurag.mysql_qa.db.models import FQAQAPair
        import jieba
        from rank_bm25 import BM25Okapi

        await DatabaseManager.ensure()
        pairs = (
            await FQAQAPair.filter(is_active=True).all().values("question", "answer")
        )
        if not pairs:
            return state

        query_tokens = list(jieba.cut(query))
        corpus = [list(jieba.cut(p["question"])) for p in pairs]
        bm25 = BM25Okapi(corpus)
        scores = bm25.get_scores(query_tokens)

        best_idx = max(range(len(scores)), key=lambda i: scores[i])
        best_raw = scores[best_idx]

        max_possible = max(scores) if scores else 1
        norm = best_raw / max_possible if max_possible > 0 else 0

        threshold = getattr(settings, "bm25_threshold_high", 0.5)
        if norm >= threshold:
            answer = pairs[best_idx]["answer"]
            await RedisManager.set_fqa(query, answer)
            logger.info(f"FQA matched: {pairs[best_idx]['question'][:40]}")
            return {
                **state,
                "synthesis_answer": answer,
                "confidence": 1.0,
                "source_references": ["FQA database"],
            }
    except Exception as e:
        logger.warning(f"FQA lookup failed (non-critical): {e}")

    return state


async def retrieve_node(state: dict) -> dict:
    sub_queries = state.get("sub_queries", [state["query"]])
    all_docs = []
    seen_ids: set[str] = set()

    strategy = ChunkStrategy.HYBRID if len(sub_queries) > 1 else ChunkStrategy.DENSE

    for sub_q in sub_queries[:3]:
        try:
            docs = await retrieve(sub_q, strategy=strategy, k=settings.retrieval_k)
            for doc in docs:
                doc_id = doc.metadata.get("id") or doc.page_content[:80]
                if doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    all_docs.append(doc)
        except Exception as e:
            logger.error(f"Retrieval failed for sub-query '{sub_q}': {e}")

    if not all_docs:
        return {**state, "retrieved_docs": [], "needs_re_retrieve": True}

    return {**state, "retrieved_docs": all_docs, "needs_re_retrieve": False}


async def evaluate_node(state: dict) -> dict:
    if not state.get("retrieved_docs"):
        return {**state, "confidence": 0.0}

    llm = _get_llm()
    chain = EVALUATE_PROMPT | llm | _output_parser()
    prompt = {
        "query": state["query"],
        "docs": _docs_to_text(state["retrieved_docs"]),
    }
    result = chain.invoke(prompt)

    confidence = float(result.get("confidence", 0.5))
    return {**state, "confidence": confidence}


async def self_critique_node(state: dict) -> dict:
    if state.get("confidence", 0.5) >= 0.8 or state.get("iteration", 0) >= state.get(
        "max_iterations", 3
    ):
        return {**state, "needs_re_retrieve": False}

    llm = _get_llm()
    chain = SELF_CRITIQUE_PROMPT | llm | _output_parser()
    result = chain.invoke(
        {
            "query": state["query"],
            "answer": state.get("synthesis_answer", ""),
            "confidence": state.get("confidence", 0.0),
        }
    )

    action = result.get("action", "retry")
    if action == "escalate_human":
        return {
            **state,
            "human_input": result.get("reason", ""),
            "needs_re_retrieve": False,
        }

    if action == "retry":
        new_queries = result.get("new_queries", [state["query"]])
        return {
            **state,
            "sub_queries": (
                new_queries if isinstance(new_queries, list) else [new_queries]
            ),
            "needs_re_retrieve": True,
        }

    return {**state, "needs_re_retrieve": False}


async def synthesize_node(state: dict) -> dict:
    llm = _get_llm()
    chain = SYNTHESIZE_PROMPT | llm | _output_parser()
    docs_text = _docs_to_text(state.get("retrieved_docs", []))

    prompt = {
        "query": state["query"],
        "context": docs_text,
        "confidence": state.get("confidence", 0.0),
    }
    result = chain.invoke(prompt)

    return {
        **state,
        "synthesis_answer": result.get("answer", result),
        "source_references": _extract_sources(state.get("retrieved_docs", [])),
    }


async def human_escalation_node(state: dict) -> dict:
    return {**state}


def _get_llm():
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        temperature=0,
    )


def _output_parser():
    from langchain_core.output_parsers import StrOutputParser

    return StrOutputParser()


def _docs_to_text(docs: list[Document]) -> str:
    return "\n\n---\n\n".join(
        f"[Source {i+1}] (score: {d.metadata.get('score', 'N/A')})\n{d.page_content}"
        for i, d in enumerate(docs[:5])
    )


def _extract_sources(docs: list[Document]) -> list[str]:
    return [
        d.metadata.get("source") or d.metadata.get("file_path") or f"chunk-{i}"
        for i, d in enumerate(docs[:3])
    ]
