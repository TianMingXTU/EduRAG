import asyncio
from langchain.agents import create_agent
from edurag.agent.llm import get_llm
from edurag.agent.prompt import SYSTEM_PROMPT
from edurag.tools.search_knowledge_base import search_knowledge_base
from edurag.mysql_qa.retrieval.bm25_search import BM25Search, _mysqlclient
from edurag.mysql_qa.cache.redis_client import redis_client


def creat_react_agent():
    return create_agent(
        model=get_llm(), tools=[search_knowledge_base], system_prompt=SYSTEM_PROMPT
    )


if __name__ == "__main__":
    _bm25_search = BM25Search()
    _bm25_search.build_index()
    agent = creat_react_agent()
    query = "简述 TCP 三次握手的过程"
    result = _bm25_search.query(query)
    if result[0]:
        print(result[0])
    else:
        message = {"messages": [{"role": "user", "content": query}]}
        result = agent.invoke(message)
        print(result)
    redis_client.close()
    asyncio.run(_mysqlclient.close())
