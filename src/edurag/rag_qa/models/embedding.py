from langchain_openai import OpenAIEmbeddings
from edurag.config.settings import config


def embedding():
    return OpenAIEmbeddings(
        model=config.embedding_model,
        api_key=config.embedding_api_key,
        base_url=config.embedding_base_url,
    )
