import os
from configparser import ConfigParser
from pathlib import Path


class Config:

    def __init__(self, path: str | None = None):
        # 显式声明实例属性
        self.llm_model: str = ""
        self.llm_api_key: str = ""
        self.llm_base_url: str = ""

        self.embedding_model: str = ""
        self.embedding_api_key: str = ""
        self.embedding_base_url: str = ""

        self._path = path or os.getenv("EDURAG_CONFIG", "config.ini")
        self._cfg = ConfigParser()
        self._load()

    def _load(self) -> None:
        if not Path(self._path).exists():
            raise FileNotFoundError(f"Config not found: {self._path}")

        self._cfg.read(self._path, encoding="utf-8")

        # 将解析出的配置正确赋值给实例变量 (self.xxx)
        self.llm_model = self._cfg.get("llm", "llm_model", fallback="")
        self.llm_api_key = self._cfg.get("llm", "llm_api_key", fallback="")
        self.llm_base_url = self._cfg.get("llm", "llm_base_url", fallback="")
        # emb
        self.embedding_model = self._cfg.get(
            "embedding", "embedding_model", fallback=""
        )
        self.embedding_api_key = self._cfg.get(
            "embedding", "embedding_api_key", fallback=""
        )
        self.embedding_base_url = self._cfg.get(
            "embedding", "embedding_base_url", fallback=""
        )

        self.parent_chunk_size = self._cfg.getint(
            "retrieval", "parent_chunk_size", fallback=1200
        )
        self.child_chunk_size = self._cfg.getint(
            "retrieval", "child_chunk_size", fallback=300
        )
        # rerank
        self.rerank_model = self._cfg.get("rerank", "rerank_model", fallback="")
        self.rerank_api_key = self._cfg.get("rerank", "rerank_api_key", fallback="")
        self.rerank_base_url = self._cfg.get("rerank", "rerank_base_url", fallback="")

        # mysql
        self.db_localhost = self._cfg.get("mysql", "host", fallback="127.0.0.1")
        self.db_port = self._cfg.get("mysql", "port", fallback=3306)
        self.db_user = self._cfg.get("mysql", "user", fallback="")
        self.db_password = self._cfg.get("mysql", "password", fallback="")
        self.db_database = self._cfg.get("mysql", "database", fallback="")

        # fqa
        self.bm25_threshold_high = self._cfg.get(
            "fqa", "bm25_threshold_high", fallback=10.0
        )
        self.bm25_threshold_low = self._cfg.get(
            "fqa", "bm25_threshold_low", fallback=0.85
        )

    def reload(self) -> None:
        self._load()


config = Config()
