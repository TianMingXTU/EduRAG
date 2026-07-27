from langchain_text_splitters import RecursiveCharacterTextSplitter
from edurag.config.settings import settings

CHINESE_SEPARATORS = ["\n\n", "\n", "。", "！", "？", "；", " ", ""]


def get_parent_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        separators=CHINESE_SEPARATORS,
        chunk_size=settings.parent_chunk_size,
        chunk_overlap=50,
    )


def get_child_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        separators=CHINESE_SEPARATORS,
        chunk_size=settings.child_chunk_size,
        chunk_overlap=25,
    )
