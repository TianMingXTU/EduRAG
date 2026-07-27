# src/edurag/mysql_qa/retrieval/bm25_search.py
import asyncio
from rank_bm25 import BM25L
from edurag.mysql_qa.db.mysql_client import MysqlClient
from edurag.mysql_qa.cache.redis_client import redis_client
from edurag.mysql_qa.utils.preprocess import tokenize
from edurag.base.config import config
from edurag.base.logger import logger

_mysqlclient = MysqlClient()


class BM25Search:
    def __init__(self):
        self.bm25 = None
        self.qa_list = []  # List[dict]
        self.threshold_high = float(config.bm25_threshold_high)
        self.threshold_low = float(config.bm25_threshold_low)

    async def build_index(self):
        """离线构建：从 MySQL 加载全量数据，分词后建 BM25 索引"""

        self.qa_list = await _mysqlclient.query_all_fqa()
        corpus = [tokenize(item["question"]) for item in self.qa_list]
        self.bm25 = BM25L(corpus)
        logger.info(f"BM25 索引构建完成，文档数: {len(self.qa_list)}")

    async def query(self, question: str) -> tuple[str | None, str | None, float | None]:
        """
        返回: (answer, source, score)
        source: "fqa_high" / "fqa_low" / "rag" / "unanswerable" / None
        """
        if not self.bm25:
            await self.build_index()

        tokens = tokenize(question)
        if not tokens:
            return None, "unanswerable", 0.0

        scores = self.bm25.get_scores(tokens)
        best_idx = scores.argmax()
        best_score = float(scores[best_idx])
        best_item = self.qa_list[best_idx]

        # 双阈值判断
        if best_score >= self.threshold_high:
            # 高置信：Redis 优先，回源 MySQL
            cached = redis_client.get(question)
            if cached:
                logger.info(f"FQA 命中 Redis 缓存，score={best_score:.2f}")
                return cached["answer"], "fqa_high", best_score

            answer = best_item["answer"]
            redis_client.set_answer(
                question,
                answer,
                best_item["subject"],
            )
            logger.info(f"FQA 高置信命中，score={best_score:.2f}，写入 Redis")
            return answer, "fqa_high", best_score
        return None, "rag", best_score
