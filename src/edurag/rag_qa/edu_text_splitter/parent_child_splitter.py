from langchain_text_splitters import RecursiveCharacterTextSplitter


def parent_child_splitter():
    parent_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""],
        chunk_size=600,
        chunk_overlap=50,
    )

    child_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""],
        chunk_size=150,
        chunk_overlap=25,
    )

    return parent_splitter, child_splitter
