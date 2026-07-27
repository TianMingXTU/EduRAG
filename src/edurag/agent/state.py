from typing import Annotated, Optional, Literal
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage
from langchain_core.documents import Document


class RetrievalState(TypedDict):
    query: str
    query_type: Literal["general_knowledge", "professional_consultation"]
    strategy: str
    sub_queries: list[str]
    retrieved_docs: list[Document]
    synthesis_answer: str
    confidence: float
    needs_re_retrieve: bool
    iteration: int
    max_iterations: int
    human_input: Optional[str]
    source_references: list[str]


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], lambda x, y: x + y]
    current_query: str
    retrieval: RetrievalState
