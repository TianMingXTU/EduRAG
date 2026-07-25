from langchain.agents import create_agent
from edurag.agent.llm import get_llm
from edurag.agent.prompt import SYSTEM_PROMPT
from edurag.tools.search_knowledge_base import search_knowledge_base


def creat_react_agent():
    return create_agent(
        model=get_llm(), tools=[search_knowledge_base], system_prompt=SYSTEM_PROMPT
    )


if __name__ == "__main__":
    agent = creat_react_agent()
    message = {"messages": [{"role": "user", "content": "EduRAG项目背景是什么?"}]}
    result = agent.invoke(message)
    print(result)
