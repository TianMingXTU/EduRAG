from langchain_text_splitters import RecursiveCharacterTextSplitter
from edurag.base.config import config


def parent_child_splitter():
    parent_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""],
        chunk_size=config.parent_chunk_size,
        chunk_overlap=50,
    )

    child_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""],
        chunk_size=config.child_chunk_size,
        chunk_overlap=25,
    )

    return parent_splitter, child_splitter
