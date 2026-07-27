from redis import Redis
import hashlib
import json
from datetime import datetime


class RedisClent:
    _instance = None
    KEY_PREFIX = "fqa:"
    DEFAULT_TTL = 3600  # 秒

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        url = "redis://localhost:6379"
        self._redis = Redis.from_url(url)

    def _make_key(self, question):
        md5 = hashlib.md5(question.strip().encode("utf-8")).hexdigest()
        return f"{self.KEY_PREFIX}{md5}"

    def set_answer(
        self, question: str, answer: str, subject: str, ttl: int = DEFAULT_TTL
    ) -> bool:
        key = self._make_key(question)
        payload = json.dumps(
            {
                "answer": answer,
                "subject": subject,
                "cached_at": datetime.now().isoformat() + "Z",
            },
            ensure_ascii=False,
        )
        return self._redis.setex(key, ttl, payload)

    def get(self, question):
        if self.exists:
            result = self._redis.getex(self._make_key(question))
            return json.loads(result)
        return f"{question} key not exists"

    def exists(self, question: str) -> bool:
        return bool(self._redis.exists(self._make_key(question)))

    def delete(self, question: str) -> int:
        return self._redis.delete(self._make_key(question))

    def close(self):
        self._redis.close()


redis_client = RedisClent()
