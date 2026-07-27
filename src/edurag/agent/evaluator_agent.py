import os
from datasets import Dataset
import sys
import types

# --- 修复 Ragas 在新版 langchain-community 下的硬编码导入崩溃 Bug ---
dummy_module = types.ModuleType("langchain_community.chat_models.vertexai")
dummy_module.ChatVertexAI = type("ChatVertexAI", (object,), {})
sys.modules["langchain_community.chat_models.vertexai"] = dummy_module
# ----------------------------------------------------------------------

from ragas import evaluate
from ragas.metrics.collections import (
    factual_correctness,
)

from langchain_community.vectorstores import FAISS

from edurag.agent.llm import get_llm
from edurag.rag_qa.models.embedding import embedding

# 1. 用 LangChain 搭建标准的 RAG 检索器与 LLM
docs_text = [
    "LangChain 是一套用于构建大语言模型应用（如 RAG、Agent）的开源 Python/JS 框架。",
    "RAGAS 是一个专门用于无监督评估 RAG 系统的开源评估工具包。",
]
vectorstore = FAISS.from_texts(docs_text, embedding=embedding())
retriever = vectorstore.as_retriever()
llm = get_llm()

# 2. 准备测试问题集
eval_questions = ["什么是 LangChain？", "RAGAS 的作用是什么？"]
ground_truths = [
    ["LangChain 是用于构建 LLM 应用的开源框架。"],
    ["RAGAS 是用于评估 RAG 系统的开源工具包。"],
]

# 3. 运行 LangChain 获取回答和上下文 (Contexts)
answers = []
contexts = []

for q in eval_questions:
    # 检索文档
    retrieved_docs = retriever.invoke(q)
    context_str_list = [doc.page_content for doc in retrieved_docs]

    # LLM 生成回答
    prompt = f"根据以下文档回答问题：\n{context_str_list}\n\n问题：{q}"
    res = llm.invoke(prompt)

    answers.append(res.content)
    contexts.append(context_str_list)

# 4. 转换为 RAGAS 识别的 Dataset 数据格式
dataset_dict = {
    "question": eval_questions,
    "answer": answers,
    "contexts": contexts,
    "ground_truth": ground_truths,
}
dataset = Dataset.from_dict(dataset_dict)

# 5. 调用 RAGAS 评估
results = evaluate(
    dataset=dataset,
    metrics=[
        factual_correctness(),
    ],
)

# 查看评估结果
df = results.to_pandas()
print(df[["question", "faithfulness", "answer_relevancy"]])
