from langchain_core.output_parsers import StrOutputParser
from edurag.agent.llm import get_llm
from edurag.rag_qa.core.prompts import query_classifier_prompt


def classify_query(query: str) -> str:
    chain = query_classifier_prompt | get_llm() | StrOutputParser()
    result = chain.invoke({"query": query})
    result = result.strip().lower()
    if result not in ("general_knowledge", "professional_consultation"):
        return "professional_consultation"
    return result
