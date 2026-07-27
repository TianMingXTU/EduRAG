计划模式已读完代码库和 2026 行业动态。以下是完整方案，请审阅后批准执行。

一、当前代码冗余与架构问题诊断
问题 位置 说明
DRY 违反 document_processor.py Processor 与 HybridProcessor 约 70% 代码重复（init、retriever、store）
DRY 违反 search_knowledge_base.py → rag_system.py tool 调用 rag_system.process()，后者又做分类→策略→检索→合成，重复了 prompt 中描述的 SOP
DRY 违反 search_fqa_bm25_rag.py + bm25_search.py 两个模块各自持有独立的 BM25Search() 实例和 DB 连接
SRP 违反 config.py Config 类同时承载 LLM/embedding/rerank/retrieval/mysql/fqa/app 七类配置
SRP 违反 agent.py main() 同时编排 BM25、Agent、Redis、MySQL 四条生命周期的关闭逻辑
全局状态 4 个模块级单例 \_bm25_search, \_mysqlclient, redis_client, \_processor — 无生命周期管理
Bug redis_client.py:44 self.exists 应为 self.exists(question)，运行时报错
安全 config.ini 硬编码 API 密钥和 MySQL 密码
Agent 循环冗余 agent.py + prompt.py System prompt 已描述 4 步 SOP（假设→检索→验证→自评），但 ReAct agent 的 tool loop 与 prompt SOP 重叠，自评步骤未真正实现为可执行的 agent 步骤
二、重构计划 (SOLID/DRY/KISS + 2026 AI 原则)
2.1 模块化拆解
src/edurag/
├── config/ # 新：独立配置层，替换扁平 Config
│ ├── **init**.py
│ ├── settings.py # Pydantic BaseSettings，从 .env + config.ini 双源加载
│ └── logging.py # 独立日志配置（非单例全局）
├── core/ # 新：业务逻辑中枢，替换 rag_system + strategy_selector + query_classifier 的耦合
│ ├── **init**.py
│ ├── orchestrator.py # 新：统一的 Agentic RAG 编排器（状态机）
│ ├── adapter.py # 新：检索策略适配器，统一 direct/hyde/subquery/backtrack/adaptive
│ └── pipeline.py # 新：RAG 流水线（ingest → retrieve → rerank → synthesize）
├── agent/ # 重构：LangGraph 状态机构建的真正 ReAct 循环
│ ├── **init**.py
│ ├── graph.py # 新：LangGraph StateGraph 定义（替换 create_agent）
│ ├── nodes.py # 新：plan / retrieve / evaluate / synthesize 节点
│ ├── state.py # 新：TypedDict 状态定义
│ └── tools/
│ ├── **init**.py
│ └── search.py # 统一检索 tool（内含策略路由）
├── storage/ # 新：数据访问层，封装 MySQL/Redis/Milvus
│ ├── **init**.py
│ ├── mysql.py # Tortoise ORM 统一入口（修复重复 init_db）
│ ├── redis.py # Redis 客户端工厂（修复 singleton bug）
│ └── vector.py # Milvus 客户端工厂
├── document/ # 新：文档处理管道
│ ├── **init**.py
│ ├── loader.py # 统一加载器（替换 doc_loader + base_loader + 各格式 loader）
│ ├── splitter.py # Parent-Child 分块（移入此处）
│ └── processor.py # 统一处理管道（合并 Processor + HybridProcessor）
├── models/ # 新：数据模型层
│ ├── **init**.py
│ ├── fqa.py # FQA QA 对（Pydantic 模型 + Tortoise 模型）
│ └── retrieval.py # 检索结果类型定义
├── prompt/ # 新：Prompt 管理
│ ├── **init**.py
│ ├── system.py # Agent System Prompt（SOP 精简为 prompt 文本）
│ └── templates.py # 所有 ChatPromptTemplate 集中管理
├── tools/ # 工具层（精简）
│ ├── **init**.py
│ └── registry.py # 新：工具注册中心（替换散落的 @tool）
├── evaluate/ # 新：评估管道（RAGAS + LLM-as-Judge）
│ ├── **init**.py
│ └── pipeline.py
└── main.py # 新：CLI 入口（替换 test.py 等散落脚本）
2.2 SOLID 落地
原则 重构动作
SRP Config → Settings + Logging 分离；Processor 拆分为 Loader/Splitter/VectorStore 各司其职
OCP 检索策略通过 Strategy 协议（Protocol 类）扩展，新增策略无需修改 orchestrator
LSP BaseLoader → DocumentLoader 协议族，子类可替换
IISP 工具注册表按需注入，agent 不依赖未使用的 module
DIP core/orchestrator.py 依赖抽象（Retriever protocol、LLM protocol），不依赖具体实现
2.3 DRY 落地
移除 search_knowledge_base.py 中对 rag_system.process() 的调用 → 统一走 orchestrator
合并 Processor/HybridProcessor 为 DocumentPipeline，通过配置开关选择是否 hybrid
BM25Search 初始化统一在 storage/mysql.py 管理 lifecycle
移除 evaluator_agent.py 独立脚本 → 集成为 evaluate/pipeline.py
2.4 2026 AI 原则落地
2026 原则 项目落地
人机协作 Agent 在 low-confidence 时主动请求 human-in-the-loop（LangGraph interrupt）
规范与测试驱动 新增 tests/ 单元测试 + RAGAS 持续评估流水线
智能资产管理 storage/vector.py + storage/mysql.py 统一管理，支持动态索引切换
可观测性 集成 LangSmith tracing + OpenTelemetry（依赖已存在但未接入）
自适应 RAG 新增 adaptive 策略：简单 query 走单 pass，复杂 query 走 agent loop
MCP 支持 tools/registry.py 支持 MCP 工具注册
三、系统架构设计（用于 README）
3.1 架构图（2026 Agentic RAG）
┌──────────────┐
│ User Query │
└──────┬───────┘
│
▼
┌─────────────────────┐
│ Adaptive Router │ ← LLM 分类：simple / complex
│ (Query Classifier) │
└──────┬──────────┬───┘
│ │
simple │ complex
│ │
▼ ▼
┌──────────────────┐ ┌──────────────────────┐
│ FQA Layer │ │ Agentic RAG Orchestrator│
│ (MySQL+BM25+ │ │ ┌─────────────────┐ │
│ Redis Cache) │ │ │ StateGraph │ │
│ < 50ms │ │ ├─ Plan Node │ │ ← LLM 分解查询
│ Zero LLM cost │ │ ├─ Retrieve Node │ │ ← 多路检索
└──────────────────┘ │ ├─ Evaluate Node │ │ ← 自评估+重试
│ ├─ Synthesize Node│ │ ← 答案合成
│ └─ Self-Critique │ │ ← 自纠错
└──────────┬─────────┘ │
│ │
▼ ▼
┌──────────────────────────┐
│ Output + Source Trace │
│ + LangSmith Trace Log │
└──────────────────────────┘

        ┌─────────────────────────────────────────────────────┐
        │  数据层（Data Layer）                                │
        │  MySQL(FQA) │ Redis(缓存) │ Milvus(向量+BM25)     │
        │  Files(PDF/MD/TXT/DOCX) │ Knowledge Graph(未来)  │
        └─────────────────────────────────────────────────────┘

3.2 核心组件说明
组件 职责 技术选型
Adaptive Router 查询分类 + 路由决策 LLM + 阈值判断
FQA Layer 高频问答极速响应 MySQL + jieba + BM25 + Redis
Agentic Orchestrator 多步规划、检索、评估、合成 LangGraph StateGraph
Hybrid Retriever 稠密+稀疏融合检索 Milvus + RRF
Reranker 精排 SiliconFlow Rerank API
Observability 可观测性 LangSmith + OpenTelemetry
Evaluation 质量评估 RAGAS + LLM-as-Judge
四、2026 工业落地创新点
基于 2026 年行业动态，在重构中融入以下创新：

4.1 核心范式：从 RAG 到 Agentic RAG
创新点 当前状态 目标状态
多步规划与自主推理 ❌ 单次检索 ✅ LangGraph 状态机，LLM 自主分解 + 多轮迭代
自适应路由 ❌ 所有查询走同一路径 ✅ 简单查询走 FQA 单 pass，复杂查询走 Agentic loop
自我反思与纠错 ⚠️ prompt 中描述但未实现 ✅ Evaluate Node + Self-Critique Node，有 confidence threshold
精准溯源 ⚠️ 仅返回片段前 100 字 ✅ 返回完整 source 引用（文档名 + 页码/段落）
可观测性 ❌ 未接入 ✅ LangSmith tracing + OpenTelemetry
4.2 新增能力模块
Multi-Tool Retrieval Router — 根据 query 类型自动路由到 Milvus / MySQL / 外部 MCP 工具
Long-Term Memory — Redis + 向量化对话历史，支持跨会话记忆
Evaluation Pipeline — RAGAS 指标自动化，CI/CD 集成
MCP Tool Registry — 标准化的外部工具注册机制
Human-in-the-Loop — Agent 在 low confidence 时中断请求人工确认
Audit Logging — 所有检索/生成决策可追溯、可回滚
4.3 工程化提升
配置管理：Pydantic Settings + .env + config.ini 双源，自动合并
安全：.env.example 模板 + 配置文件排除 secrets
异步基础设施：全 async 栈，修复已有 async/sync 混用 bug
测试：新增 tests/ 单元测试 + 集成测试
部署：更新的 docker-compose.yml + Dockerfile
五、执行顺序
Phase 1（重构）: 配置层 + 存储层 + 文档层 → 打通数据访问
Phase 2（重构）: 核心编排器 + Agent 状态机 → 替换 create_agent
Phase 3（重构）: 工具层 + 评估层 → 统一入口 + 可观测性
Phase 4（创新）: Agentic RAG 闭环 + 自适应路由 + 长期记忆
Phase 5（文档）: 更新 README + 架构图 + 部署指南
每个 phase 完成后都有可运行的 check（assert-based demo() 或 pytest）。
