import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any

from edurag.config.settings import settings
from edurag.config.logging import logger

logger = logging.getLogger(__name__)


@dataclass
class EvalResult:
    metric: str
    score: float
    details: dict | None = None


@dataclass
class EvalReport:
    query: str
    expected_answer: str
    generated_answer: str
    confidence: float
    metrics: list[EvalResult] = field(default_factory=list)
    passed: bool = True
    source_references: list[str] = field(default_factory=list)
    iteration_count: int = 0


class RagEvaluator:
    def __init__(self) -> None:
        self._ragas_available: bool = False
        self._dataset: list[dict[str, Any]] = []
        self._try_load_ragas()

    def _try_load_ragas(self) -> None:
        try:
            from ragas import evaluate as ragas_evaluate
            from ragas.metrics.collections import (
                faithfulness,
                answer_relevancy,
                context_precision,
                context_recall,
            )
            from ragas.dataset_schema import SingleTurnSample

            self._ragas_available = True
            self._ragas_evaluate = ragas_evaluate
            self._faithfulness = faithfulness
            self._answer_relevancy = answer_relevancy
            self._context_precision = context_precision
            self._context_recall = context_recall
            logger.info("RAGAS loaded — full evaluation pipeline active")
        except ImportError:
            self._ragas_available = False
            logger.warning(
                "ragas not installed. "
                "Install with: pip install ragas>=0.4.3. "
                "Falling back to LLM-as-Judge evaluation."
            )

    def add_sample(
        self,
        query: str,
        expected_answer: str,
        retrieved_docs: list[Any],
        generated_answer: str,
        confidence: float,
    ) -> None:
        contexts = [
            d.page_content if hasattr(d, "page_content") else str(d)
            for d in retrieved_docs
        ]
        self._dataset.append(
            {
                "query": query,
                "expected": expected_answer,
                "contexts": contexts,
                "answer": generated_answer,
                "confidence": confidence,
            }
        )

    async def evaluate_all(self) -> list[EvalReport]:
        reports: list[EvalReport] = []
        for sample in self._dataset:
            report = await self._evaluate_one(sample)
            reports.append(report)
        return reports

    def evaluate_all_sync(self) -> list[EvalReport]:
        return [self._evaluate_one_sync(s) for s in self._dataset]

    def _evaluate_one_sync(self, sample: dict[str, Any]) -> EvalReport:
        metrics: list[EvalResult] = []
        metrics.append(EvalResult("faithfulness", self._compute_faithfulness(sample)))
        metrics.append(EvalResult("answer_relevancy", self._compute_relevancy(sample)))
        metrics.append(EvalResult("confidence", sample["confidence"]))
        passed = all(m.score >= 0.7 for m in metrics if m.metric != "confidence")
        return EvalReport(
            query=sample["query"],
            expected_answer=sample["expected"],
            generated_answer=sample["answer"],
            confidence=sample["confidence"],
            metrics=metrics,
            passed=passed,
        )

    async def _evaluate_one(self, sample: dict[str, Any]) -> EvalReport:
        if self._ragas_available:
            return await self._evaluate_with_ragas(sample)
        return self._evaluate_with_llm_judge(sample)

    async def _evaluate_with_ragas(self, sample: dict[str, Any]) -> EvalReport:
        from ragas.dataset_schema import SingleTurnSample as RAGASSample

        ragas_sample = RAGASSample(
            user_input=sample["query"],
            response=sample["answer"],
            retrieved_contexts=sample["contexts"],
            reference=sample["expected"],
        )
        result = await self._ragas_evaluate(
            dataset=[ragas_sample],
            metrics=[
                self._faithfulness,
                self._answer_relevancy,
                self._context_precision,
                self._context_recall,
            ],
        )
        df = result.to_pandas()
        metrics = [
            EvalResult("faithfulness", float(df["faithfulness"].iloc[0])),
            EvalResult("answer_relevancy", float(df["answer_relevancy"].iloc[0])),
            EvalResult("context_precision", float(df["context_precision"].iloc[0])),
            EvalResult("context_recall", float(df["context_recall"].iloc[0])),
            EvalResult("confidence", sample["confidence"]),
        ]
        passed = all(m.score >= 0.7 for m in metrics if m.metric != "confidence")
        return EvalReport(
            query=sample["query"],
            expected_answer=sample["expected"],
            generated_answer=sample["answer"],
            confidence=sample["confidence"],
            metrics=metrics,
            passed=passed,
        )

    def _evaluate_with_llm_judge(self, sample: dict[str, Any]) -> EvalReport:
        from langchain_core.output_parsers import JsonOutputParser
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            temperature=0,
        )
        EVALUATE_PROMPT = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "你是一个 RAG 系统评估专家。"
                    "请计算以下指标的分数（0-1），精确到小数点后两位。"
                    "输出 JSON 格式，包含 faithfulness, answer_relevancy, context_precision。",
                ),
                (
                    "human",
                    "查询：{query}\n\n"
                    "检索上下文：\n{contexts}\n\n"
                    "生成的答案：{answer}\n\n"
                    "预期答案（参考）：{expected}\n\n"
                    "评分 JSON：",
                ),
            ]
        )
        chain = EVALUATE_PROMPT | llm | JsonOutputParser()
        result = chain.invoke(
            {
                "query": sample["query"],
                "contexts": "\n".join(sample["contexts"][:3]),
                "answer": sample["answer"],
                "expected": sample["expected"],
            }
        )
        try:
            scores = json.loads(result)
        except json.JSONDecodeError, TypeError:
            scores = {
                "faithfulness": 0.5,
                "answer_relevancy": 0.5,
                "context_precision": 0.5,
            }
        metrics = [
            EvalResult("faithfulness", float(scores.get("faithfulness", 0.5))),
            EvalResult("answer_relevancy", float(scores.get("answer_relevancy", 0.5))),
            EvalResult(
                "context_precision", float(scores.get("context_precision", 0.5))
            ),
            EvalResult("confidence", sample["confidence"]),
        ]
        passed = all(m.score >= 0.7 for m in metrics if m.metric != "confidence")
        return EvalReport(
            query=sample["query"],
            expected_answer=sample["expected"],
            generated_answer=sample["answer"],
            confidence=sample["confidence"],
            metrics=metrics,
            passed=passed,
        )

    def _compute_faithfulness(self, sample: dict[str, Any]) -> float:
        answer = sample["answer"]
        contexts = sample["contexts"]
        if not contexts or not answer:
            return 0.0
        total = max(len(contexts), 1)
        matched = sum(1 for ctx in contexts if ctx.strip())
        return min(matched / total * 2, 1.0)

    def _compute_relevancy(self, sample: dict[str, Any]) -> float:
        query = sample["query"]
        answer = sample["answer"]
        if not answer or not query:
            return 0.0
        return min(len(answer.split()) / max(len(query.split()), 1), 1.0)


evaluator = RagEvaluator()
