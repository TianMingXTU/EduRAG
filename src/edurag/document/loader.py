from pathlib import Path
from abc import ABC, abstractmethod
from langchain_core.documents import Document

LOADER_MAP = {
    ".pdf": "PyPDFLoader",
    ".docx": "Docx2txtLoader",
    ".doc": "Docx2txtLoader",
    ".md": "TextLoader",
    ".txt": "TextLoader",
}

LOADER_MAPPING = {
    ".pdf": ("langchain_community.document_loaders", "PyPDFLoader"),
    ".docx": ("langchain_community.document_loaders", "Docx2txtLoader"),
    ".doc": ("langchain_community.document_loaders", "Docx2txtLoader"),
    ".md": ("langchain_community.document_loaders", "TextLoader"),
    ".txt": ("langchain_community.document_loaders", "TextLoader"),
}


class DocumentLoadError(ValueError):
    pass


def _get_loader(ext: str):
    if ext not in LOADER_MAPPING:
        raise DocumentLoadError(
            f"Unsupported file type: {ext}. Supported: {list(LOADER_MAPPING)}"
        )
    module_path, class_name = LOADER_MAPPING[ext]
    module = __import__(module_path, fromlist=[class_name])
    return getattr(module, class_name)


async def load_documents(file_path: str | Path) -> list[Document]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Document not found: {path}")
    if path.is_dir():
        docs = []
        for f in sorted(path.iterdir()):
            if f.suffix in LOADER_MAPPING:
                docs.extend(await _load_single_file(f))
        return docs
    return await _load_single_file(path)


async def _load_single_file(path: Path) -> list[Document]:
    ext = path.suffix.lower()
    loader_cls = _get_loader(ext)
    loader = loader_cls(str(path))
    return loader.load()
