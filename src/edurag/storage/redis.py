import redis.asyncio as aioredis
from edurag.config import settings
import hashlib
import json
import time


class RedisManager:
    _client = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            cls._client = aioredis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
        return cls._client

    @classmethod
    async def close(cls) -> None:
        if cls._client is not None:
            await cls._client.close()
            cls._client = None

    @staticmethod
    def _make_key(question: str, namespace: str = "fqa") -> str:
        normalized = " ".join(sorted(question.strip().split()))
        return f"{namespace}:{hashlib.sha256(normalized.encode()).hexdigest()}"

    @classmethod
    async def get_fqa(cls, question: str):
        return await cls.get_client().get(cls._make_key(question))

    @classmethod
    async def set_fqa(cls, question: str, answer: str, ttl: int = 3600):
        await cls.get_client().setex(
            cls._make_key(question),
            ttl,
            json.dumps({"answer": answer, "cached_at": time.time()}),
        )

    @classmethod
    async def delete_fqa(cls, question: str) -> int:
        return await cls.get_client().delete(cls._make_key(question))

    @classmethod
    async def health_check(cls) -> bool:
        try:
            return await cls.get_client().ping()
        except Exception:
            return False


def create_redis_client() -> RedisManager:
    return RedisManager()
