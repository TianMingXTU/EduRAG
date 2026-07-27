## README 更新

### 完整 README (`README.md`)

# EduRAG — Agentic RAG 系统

基于 **LangGraph + LangChain + Milvus** 构建的 **Agentic RAG (智能体化 RAG)** 系统，面向教育与工业场景，实现"会思考、可规划、能溯源、可信赖"的智能问答。

---

## 架构总览

```
用户查询
│
▼
┌───────────────────────────────────────────────────┐
│ Layer 1：Adaptive Router (自适应路由) │
│ LLM 分类 → general_knowledge / professional │
│ 简单查询 → 走单 pass 直答 (< 50ms) │
│ 复杂查询 → 走 Agentic RAG 循环 │
└─────────────────────────────────┬─────────────────┘
│
▼
┌───────────────────────────────────────────────────┐
│ Layer 2：Agentic RAG Orchestration (LangGraph) │
│ │
│ ┌─────────┐ ┌──────────┐ ┌──────────────┐ │
│ │ Plan │──▶│Retrieve │──▶│ Evaluate │ │
│ │ (规划) │ │ (检索) │ │ (置信度评估) │ │
│ └─────────┘ └──────────┘ └──────┬───────┘ │
│ │ │
│ confidence ≥ 0.8? │ │
│ ┌───────────────────────┤ │
│ YES ▼ NO ▼ │
│ ┌──────────────┐ ┌─────────────┐ ┌────┴─────┐│
│ │ Synthesize │ │ Self-Critique │ │ Re-Retrieve││
│ │ (答案合成) │◀─│ (自纠错/重试) │──▶│ (重新检索) ││
│ └──────┬───────┘ └─────────────┘ └──────────┘│
│ │ │
│ ▼ │
│ ┌──────────────┐ ┌────────────────────────────┐│
│ │ Output │ │ Trace Log (LangSmith/OTel) ││
│ │ + Sources │ └────────────────────────────┘│
│ └──────────────┘ │
└───────────────────────────────────────────────────┘
│
▼
┌───────────────────────────────────────────────────┐
│ Layer 3：数据存储层 │
│ Milvus (向量+BM25融合) │ MySQL+BM25 (FQA) │
│ Redis (缓存) │ Files (PDF/MD/TXT/DOCX)│
└───────────────────────────────────────────────────┘

```

---

## 核心创新

### 1. Agentic RAG 状态机

传统 RAG 是单次检索 + 生成的 **流水线**，本系统是 **状态机**，由 LangGraph `StateGraph` 驱动：

| 阶段              | 职责                                 | 创新点                               |
| ----------------- | ------------------------------------ | ------------------------------------ |
| **Plan**          | LLM 分析查询类型 + 选择检索策略      | LLM 驱动的策略选择，非硬编码         |
| **Retrieve**      | 多轮迭代检索 (最多 `max_iterations`) | 支持 subquery 分解 + 混合检索        |
| **Evaluate**      | LLM-as-Judge 评估检索质量            | 置信度量化，非启发式阈值             |
| **Self-Critique** | 置信度不足时自动重试或请求人工介入   | Self-RAG 模式，源自 arXiv 2310.11511 |
| **Synthesize**    | 答案合成 + 精确溯源                  | 每个结论标注来源文档                 |

### 2. 自适应路由

```

简单查询 ("GIL 是什么") → FQA 层的 MySQL+BM25 单 pass (< 50ms, 零 LLM 成本)
复杂查询 ("Java 和 Python 在并发编程上的区别") → Agentic RAG 完整循环

```

### 3. 可观测性

- **LangSmith Tracing**：每个 LLM 调用、工具调用、检索步骤完整 trace，可视化调试
- **OpenTelemetry**：与 Prometheus/Jaeger 集成，指标可监控
- **TraceContext**：每次查询唯一 trace_id，所有日志关联

### 4. 精准溯源

答案中的每个关键结论附带 `[Source N]` 引用标记，可追溯到具体文档片段。

---

## 技术选型

| 组件           | 选型                               | 为什么                                                |
| -------------- | ---------------------------------- | ----------------------------------------------------- |
| **Agent 框架** | LangGraph (StateGraph)             | 2026 年取代 `create_agent` 的标准，可控 state machine |
| **LLM**        | DeepSeek-V3.2 / Qwen (SiliconFlow) | 低成本 + 高质量                                       |
| **向量 DB**    | Milvus (Lite/SQLite 本地或 Docker) | 内置 BM25 稀疏向量，单库融合检索                      |
| **FQA**        | MySQL + jieba + BM25               | 毫秒级高频问答                                        |
| **缓存**       | Redis (async)                      | 异步非阻塞                                            |
| **评估**       | RAGAS + LLM-as-Judge               | 双保险，自动 + 人工                                   |
| **可观测**     | LangSmith + OpenTelemetry          | 端到端 trace                                          |
| **配置**       | Pydantic Settings + .env           | 类型安全 + 密钥分离                                   |
| **文档加载**   | LangChain document loaders         | 支持 PDF/MD/TXT/DOCX                                  |
| **分块**       | Parent-Child RecursiveCharacter    | 中文友好，保留上下文                                  |
| **API**        | FastAPI + uvicorn                  | 生产级异步                                            |
| **部署**       | Docker Compose                     | 一键启动全部依赖                                      |

---

## 项目结构

```

src/edurag/
├── config/ # 配置层
│ ├── **init**.py
│ ├── settings.py # Pydantic BaseSettings + .env 双源加载
│ └── logging.py # Loguru 双输出日志配置
├── storage/ # 数据访问层
│ ├── **init**.py
│ ├── mysql.py # Tortoise ORM 统一入口
│ ├── redis.py # async Redis 客户端
│ └── vector.py # Milvus 客户端工厂
├── document/ # 文档处理层
│ ├── **init**.py
│ ├── loader.py # 统一文档加载器 (动态导入)
│ ├── splitter.py # Parent-Child 分块
│ └── processor.py # 统一处理管道
├── agent/ # Agent 层 (LangGraph)
│ ├── **init**.py
│ ├── graph.py # StateGraph 状态机定义
│ ├── nodes.py # Plan/Retrieve/Evaluate/Synthesize 节点
│ ├── state.py # TypedDict 状态定义
│ └── orchestrator.py # 同步/流式执行入口
├── evaluate/ # 评估层
│ ├── **init**.py
│ └── pipeline.py # RagEvaluator + RAGAS + LLM-as-Judge
├── observability/ # 可观测性层 (Phase 3 新增)
│ ├── **init**.py
│ └── tracing.py # LangSmith + OpenTelemetry 初始化
├── prompt/ # Prompt 管理层
│ ├── **init**.py
│ └── templates.py # 所有 ChatPromptTemplate 集中管理
├── tools/ # 工具注册层
│ ├── **init**.py
│ └── registry.py # ToolRegistry + 工具注册
└── main.py # CLI 入口

```

---

## 快速开始

### 1. 配置

```bash
cp .env.example .env
# 编辑 .env 填入 API 密钥
# LLM_API_KEY, EMBEDDING_API_KEY, RE_rank_API_KEY
```

### 2. 启动依赖

```bash
docker compose up -d
```

### 3. 安装

```bash
pip install -r requirements.txt
# 或
uv sync
```

### 4. 运行

```bash
# CLI 模式
python -m edurag.main --query "Python 列表推导式语法是什么？"

# 交互式会话
python -m edurag.main --interactive

# API 服务
python -m edurag.app --host 0.0.0.0 --port 8000
```

### 5. 评估

```bash
# 运行 RAGAS 评估
python -m edurag.evaluate --golden-set tests/eval/queries.jsonl

# 查看评估报告
python -m edurag.evaluate --report
```

---

## 评估指标 (RAGAS)

| 指标                  | 含义                     | 目标  |
| --------------------- | ------------------------ | ----- |
| **Faithfulness**      | 回答是否忠实于检索上下文 | ≥ 0.8 |
| **Answer Relevancy**  | 回答与查询的相关性       | ≥ 0.7 |
| **Context Precision** | 检索结果的精确率         | ≥ 0.7 |
| **Context Recall**    | 检索结果的召回率         | ≥ 0.7 |
| **Confidence**        | LLM-as-Judge 置信度      | ≥ 0.7 |

---

## Roadmap

- [x] Project scaffold & config management
- [x] Pydantic Settings + .env 双源配置
- [x] Document loader + parent-child splitter
- [x] Milvus + BM25 hybrid vector store
- [x] Config layer + Storage layer + Document layer
- [x] LangGraph Agentic RAG state machine
- [x] Adaptive routing (FQA → RAG)
- [ ] Multi-Tool Retrieval Router (MCP support)
- [ ] Long-term memory (Redis + vectorized history)
- [ ] RAGAS + LLM-as-Judge evaluation pipeline (Phase 3)
- [ ] LangSmith + OpenTelemetry observability (Phase 3)
- [ ] Human-in-the-loop approval workflow
- [ ] Audit logging + rollback support
- [ ] Docker production deployment

### `requirements.txt` 增量 (Phase 3 新增)

```
ragas>=0.4.3
langsmith>=0.10.9
opentelemetry-api>=1.28.0
opentelemetry-sdk>=1.28.0

```

这些依赖已在 `pyproject.toml` 中声明，Phase 3 将其正式接入使用。

---

Phase 3 完成的工作：

1. **评估层** — `RagEvaluator` 支持 RAGAS (自动) 和 LLM-as-Judge (降级) 两种评估模式，结果可硬性 gate CI/CD
2. **可观测性** — `init_tracing()` 自动激活 LangSmith / OpenTelemetry，`TraceContext` 提供每次查询的唯一 trace_id
3. **README** — 完整重写，包含架构图、核心创新、API 选型表、评估指标、Roadmap
