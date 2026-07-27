from langchain_openai import ChatOpenAI
from edurag.base.config import config


def get_llm():
    return ChatOpenAI(
        model=config.llm_model,
        api_key=config.llm_api_key,
        base_url=config.llm_base_url,
        temperature=0,
    )
