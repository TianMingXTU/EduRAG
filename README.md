# EduRAG — 企业级智能教育问答系统

基于 **LangGraph + LangChain + Milvus** 构建的双层 RAG 问答系统，面向 IT 教育培训场景，融合高频问答（FQA）与深度检索（RAG），实现精准、可溯源、低幻觉的智能答疑。

---

## Architectural Overview

```
用户问题
    │
    ▼
┌─────────────────────────────────────────┐
│         FQA System（高频问答匹配层）        │
│  MySQL + jieba 分词 + BM25 相似度检索       │
│  + Redis 缓存                             │
│                                           │
│  相似度 ≥ 阈值 → 直接返回缓存答案            │
│  相似度 < 阈值 → 下放 RAG System            │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│      RAG System（深度语义检索层）           │
│                                           │
│  ├─ 1. Query Classification               │
│  │  ┌ 通用知识 → 直答 LLM                 │
│  │  └ 专业咨询 → 进入检索流程              │
│  │                                         │
│  ├─ 2. Strategy Selection (LLM-driven)     │
│  │  ┌ DirectRetrieval   — 明确查询         │
│  │  ├ HyDE              — 抽象问题         │
│  │  ├ SubQuery          — 复杂查询         │
│  │  └ Backtrack         — 冗余问题         │
│  │                                         │
│  ├─ 3. Query Optimization (LLM)            │
│  │  → 重写 / 扩展 / 分解用户问题           │
│  │                                         │
│  ├─ 4. Hybrid Retrieval                    │
│  │  ┌ Dense  (Milvus + Embedding)          │
│  │  ├ Sparse (BM25 + jieba)                │
│  │  └ RRF Ranker 融合排序                   │
│  │                                         │
│  ├─ 5. Prompt Assembly                     │
│  │  → query + context + history            │
│  │                                         │
│  └─ 6. LLM Generation                      │
│     → Final Answer / 人工引导               │
└─────────────────────────────────────────┘
```

---

## Innovation Highlights

### 1. LangGraph ReAct Agent — 超越传统 Chain

传统 RAG（含本教材基础版）使用固定的 `prompt | llm` 链式调用，无法自主判断是否需要检索。

本项目采用 **LangGraph ReAct Agent** 作为核心引擎：

| 维度 | 教材基础版 | 本项目 |
|------|-----------|--------|
| 控制流 | 固定 Chain | Agent 自主决策 |
| 检索时机 | 每次都检索 | 按需调用工具 |
| 查询优化 | 手动编写 | Agent 自动重写 |
| 多轮补充 | 不支援 | 自动二次检索 |
| 状态管理 | 无 | MemorySaver 持久化 |

Agent 的工作流：

```
用户输入
  │
  ├─ 是否需要知识库？ ──→ 否 ──→ LLM 直接回答
  │
  └─ 是 ──→ 调用 query_rag 工具
              │
              ├─ query_rag(key: str)
              │    └─ Hybrid Search → 返回文档片段
              │
              └─ 结果充分？──→ 否 ──→ 重新优化关键词，二次检索
                                └─ 是 ──→ LLM 整合生成
```

### 2. Hybrid Search with RRF Reranking

单一向量检索的局限：语义相似 ≠ 答案相关。本项目实现 **稠密 + 稀疏融合检索**：

```
Query
  ├──→ Embedding Model ──→ Dense Vector ──→ Milvus ANN Search
  │                                              │
  └──→ jieba 分词 ──→ BM25 Sparse Vector ──→ Milvus Keyword Search
                                                   │
                                              RRF Reciprocal Rank Fusion
                                                   │
                                              Final Ranked Results
```

- **Dense**：Qwen3-Embedding / bge-m3，捕获语义
- **Sparse**：BM25 + jieba 分词，捕获关键词精确匹配
- **Rerank**：RRF（Reciprocal Rank Fusion）综合排序

### 3. Parent-Child Chunking 策略

```
原始文档
    │
    ▼
┌────────────────┐
│  Parent Chunks │  ← chunk_size=1200, overlap=50
│  (完整上下文)   │
└───────┬────────┘
        │ 继续切分
        ▼
┌────────────────┐
│  Child Chunks  │  ← chunk_size=300, overlap=50
│  (精确片段)     │
└───────┬────────┘
        │ 向量化 → Milvus
        ▼
   检索子块 → 返回父块全文 → 兼顾精确度与上下文完整性
```

### 4. LLM-Driven 多策略选择

不硬编码单一检索策略，而是让 **LLM 动态决策** 最佳策略：

```
问题类型          LLM 判断         执行策略
─────────────────────────────────────────────
"Python 列表推导式语法"   →  明确  →  DirectRetrieval
"怎么优化代码性能"        →  抽象  →  HyDE（生成假设答案再检索）
"Java 和 Python 在并发   →  复杂  →  SubQuery（拆解为多个子问题）
 编程上的区别是什么"
"嗯…就是那个…我之前      →  冗余  →  Backtrack（提取核心后检索）
 看到的那个功能"
```

### 5. Two-Layer Fallback Architecture

```
User Query
    │
    ▼
┌──────────────┐
│  FQA Layer   │──→ Match Found (score ≥ threshold) ──→ Direct Answer
│  MySQL+BM25  │                                           (0.1s)
│  Redis Cache │
└──────┬───────┘
       │ No good match
       ▼
┌──────────────┐
│  RAG Layer   │──→ Hybrid Search → LLM Generation
│  Milvus+LLM  │                                           (3-10s)
└──────────────┘
```

- **FQA** 覆盖高频标准问答，毫秒级响应，零 LLM 成本
- **RAG** 处理长尾/复杂问题，保证回答质量
- **Redis** 缓存热点查询，避免重复计算

### 6. 工程化基础设施

| 模块 | 实现 |
|------|------|
| **配置管理** | `configparser` + `os.getenv` 双覆盖，Docker 友好 |
| **日志系统** | 控制台 + 文件双输出，支持 DEBUG/INFO/WARNING/ERROR 分级 |
| **多格式文档** | PDF / TXT / DOCX / Markdown 统一加载接口 |
| **API 服务** | FastAPI + uvicorn，生产级 REST 接口 |
| **容器化部署** | Docker Compose 编排 Milvus + Redis + MySQL + App |

### 7. RAGAS 评估体系

集成 RAGAS 框架，量化评估 RAG 各环节质量：

| 指标 | 含义 |
|------|------|
| **Faithfulness** | 回答是否忠实于检索上下文 |
| **Answer Relevancy** | 回答与问题的相关性 |
| **Context Precision** | 检索结果的精确率 |
| **Context Recall** | 检索结果的召回率 |

---

## Project Structure

```
src/edurag/
├── base/                       # 基础设施层
│   ├── config.py               # ConfigParser + 环境变量覆盖
│   └── logger.py               # 双输出日志
├── agent/                      # LangGraph Agent 层
│   ├── llm.py                  # ReAct Agent 创建
│   └── prompt.py               # System Prompt（SOP 驱动）
├── rag_qa/                     # RAG 核心层
│   ├── core/
│   │   ├── document_processor.py   # 父子分块
│   │   ├── vector_store.py         # Milvus + BM25 混合检索
│   │   ├── prompts.py              # Prompt 模板
│   │   ├── query_classifier.py     # 查询分类（LLM/BERT）
│   │   ├── strategy_selector.py    # 4 种策略选择
│   │   └── rag_system.py           # RAG 编排
│   ├── edu_document_loaders/
│   ├── edu_text_spliter/
│   ├── models/
│   └── rag_assesment/              # RAGAS 评估
├── tools/                       # LangChain 工具
│   └── query_rag.py             # 知识库检索工具
├── mysql_qa/                    # FQA 系统
│   ├── db/mysql_client.py
│   ├── cache/redis_client.py
│   ├── retrieval/bm25_search.py
│   └── utils/preprocess.py
├── main.py                     # CLI 入口
└── app.py                      # FastAPI 服务
```

---

## Tech Stack

| Category | Choice |
|----------|--------|
| LLM | DeepSeek-V3.2 / Qwen（SiliconFlow API） |
| Agent Framework | LangGraph ReAct Agent |
| Vector Database | Milvus（Docker） |
| Embedding | Qwen3-Embedding / bge-m3 |
| Hybrid Search | Dense + BM25 Sparse + RRF |
| FQA Storage | MySQL + Redis Cache |
| Tokenization | jieba |
| API Layer | FastAPI + uvicorn |
| Deployment | Docker Compose |
| Evaluation | RAGAS |
| Python Env | uv / poetry, Python >= 3.10 |

---

## Quick Start

### Prerequisites

- Python >= 3.10
- Docker & Docker Compose
- SiliconFlow / DashScope API Key

### Start Middleware

```bash
docker compose up -d
```

### Install

```bash
pip install -r requirements.txt
```

### Configure

```bash
cp config.ini.example config.ini
# edit your API keys
# or via env:
export LLM_API_KEY=sk-xxx
export EMBEDDING_API_KEY=sk-xxx
```

## Build Knowledge Base

```bash
python -m edurag.rag_qa.core.vector_store
```

### Run

```bash
# CLI Mode
python -m edurag.main

# API Service
python -m edurag.app
```

---

## Roadmap

- [x] Project scaffold & config management
- [x] Document loader with parent-child chunking
- [x] Milvus hybrid vector store
- [x] LangGraph ReAct Agent with query_rag tool
- [ ] Query classifier (LLM-based)
- [ ] 4-strategy selector & query optimizer
- [ ] FQA system (MySQL + BM25 + Redis)
- [ ] Dual-layer fusion (FQA → RAG)
- [ ] FastAPI with streaming output
- [ ] RAGAS evaluation pipeline
- [ ] Docker production deployment
