import os
from pathlib import Path
from functools import cached_property

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    llm_model: str = ""
    llm_api_key: str = ""
    llm_base_url: str = ""

    embedding_model: str = ""
    embedding_api_key: str = ""
    embedding_base_url: str = ""

    rerank_model: str = ""
    rerank_api_key: str = ""
    rerank_base_url: str = ""

    parent_chunk_size: int = 1200
    child_chunk_size: int = 300
    chunk_overlap: int = 50
    retrieval_k: int = 5

    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = ""
    mysql_password: str = ""
    mysql_database: str = "edu_rag"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0

    MILVUS_DB_PATH: str = "./milvus_demo_db"
    milvus_collection: str = "langchain_milvus_demo"
    milvus_collection_hybrid: str = "langchain_hy_milvus_demo"

    bm25_threshold_high: float = 10.0
    bm25_threshold_low: float = 0.85

    @property
    def mysql_dsn(self) -> str:
        return (
            f"mysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}?charset=utf8mb4"
        )

    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @field_validator("mysql_password", "redis_password", mode="before")
    @classmethod
    def _strip_quotes(cls, v):
        if isinstance(v, str) and len(v) >= 2 and v[0] == v[-1] and v[0] in ('"', "'"):
            return v[1:-1]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        env_nested_delimiter = "__"

    @classmethod
    def reload(cls) -> "Settings":
        return cls(_env_file=cls._SettingsConfigDirective.env_file)


settings = Settings()
