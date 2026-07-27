import json
from typing import AsyncIterator
from edurag.config.settings import settings
from edurag.agent.graph import graph
from edurag.config.logging import logger
from edurag.storage.redis import RedisManager


async def run_agent(query: str, max_iterations: int = 3) -> dict:
    initial_state = {
        "query": query,
        "query_type": "",
        "strategy": "",
        "sub_queries": [query],
        "retrieved_docs": [],
        "synthesis_answer": "",
        "confidence": 0.0,
        "needs_re_retrieve": False,
        "iteration": 0,
        "max_iterations": max_iterations,
        "human_input": None,
        "source_references": [],
    }

    state = initial_state
    async for event in graph.astream({"retrieval": state}):
        node_name = list(event.keys())[0] if event else "unknown"
        if node_name != "__end__":
            logger.info(f"Agent node executed: {node_name}")
        state = event.get(node_name, state)

    result = {
        "answer": state.get("synthesis_answer", ""),
        "confidence": state.get("confidence", 0.0),
        "strategy": state.get("strategy", ""),
        "sources": state.get("source_references", []),
        "iterations": state.get("iteration", 0),
    }

    try:
        await RedisManager.set_fqa(query, result["answer"])
    except Exception as e:
        logger.warning(f"Failed to cache result in Redis: {e}")

    return result


async def run_agent_stream(query: str, max_iterations: int = 3) -> AsyncIterator[dict]:
    initial_state = {
        "query": query,
        "query_type": "",
        "strategy": "",
        "sub_queries": [query],
        "retrieved_docs": [],
        "synthesis_answer": "",
        "confidence": 0.0,
        "needs_re_retrieve": False,
        "iteration": 0,
        "max_iterations": max_iterations,
        "human_input": None,
        "source_references": [],
    }

    state = initial_state
    async for event in graph.astream({"retrieval": state}):
        node_name = list(event.keys())[0] if event else "unknown"
        if node_name == "synthesize":
            yield {
                "type": "final_answer",
                "answer": state.get("synthesis_answer", ""),
                "confidence": state.get("confidence", 0.0),
                "sources": state.get("source_references", []),
            }
        elif node_name == "human_escalation":
            yield {
                "type": "human_input_requested",
                "reason": state.get("human_input", ""),
            }
        else:
            yield {"type": "node_progress", "node": node_name}
