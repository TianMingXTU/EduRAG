from langgraph.graph import StateGraph, END
from edurag.agent.state import AgentState
from edurag.agent.nodes import (
    plan_node,
    fqa_lookup_node,
    retrieve_node,
    evaluate_node,
    synthesize_node,
    self_critique_node,
    human_escalation_node,
)
from edurag.config.settings import settings


def _route_after_plan(state: AgentState) -> str:
    qtype = state["retrieval"].get("query_type", "professional_consultation")
    if qtype == "general_knowledge":
        return "fqa_lookup"
    return "retrieve"


def _route_after_fqa(state: AgentState) -> str:
    if state["retrieval"].get("synthesis_answer"):
        return "synthesize"
    return "retrieve"


def _route_after_retrieve(state: AgentState) -> str:
    if not state["retrieval"].get("retrieved_docs"):
        return "synthesize"
    return "evaluate"


def _route_after_evaluate(state: AgentState) -> str:
    confidence = state["retrieval"].get("confidence", 0.0)
    iteration = state["retrieval"].get("iteration", 0)
    max_iters = state["retrieval"].get("max_iterations", 3)

    if confidence >= 0.8:
        return "synthesize"
    if iteration >= max_iters:
        return "synthesize"
    return "self_critique"


def _route_after_critique(state: AgentState) -> str:
    if state["retrieval"].get("human_input"):
        return "human_escalation"
    if state["retrieval"].get("needs_re_retrieve"):
        return "retrieve"
    return "synthesize"


def build_graph() -> StateGraph:
    workflow = StateGraph(AgentState)

    workflow.add_node("plan", plan_node)
    workflow.add_node("fqa_lookup", fqa_lookup_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("evaluate", evaluate_node)
    workflow.add_node("synthesize", synthesize_node)
    workflow.add_node("self_critique", self_critique_node)
    workflow.add_node("human_escalation", human_escalation_node)

    workflow.set_entry_point("plan")

    workflow.add_conditional_edges(
        "plan",
        _route_after_plan,
        {"fqa_lookup": "fqa_lookup", "retrieve": "retrieve"},
    )

    workflow.add_conditional_edges(
        "fqa_lookup",
        _route_after_fqa,
        {"synthesize": "synthesize", "retrieve": "retrieve"},
    )

    workflow.add_conditional_edges(
        "retrieve",
        _route_after_retrieve,
        {"evaluate": "evaluate", "synthesize": "synthesize"},
    )

    workflow.add_conditional_edges(
        "evaluate",
        _route_after_evaluate,
        {"self_critique": "self_critique", "synthesize": "synthesize"},
    )

    workflow.add_conditional_edges(
        "self_critique",
        _route_after_critique,
        {
            "retrieve": "retrieve",
            "synthesize": "synthesize",
            "human_escalation": "human_escalation",
        },
    )

    workflow.add_edge("synthesize", END)
    workflow.add_edge("human_escalation", END)

    return workflow.compile(checkpointer=None)


graph = build_graph()
