from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

PLAN_SYSTEM = """你是一个查询规划器。请分析用户查询并决定：

1. query_type: "general_knowledge" 或 "professional_consultation"
2. strategy: direct（明确）/ hyde（抽象）/ subquery（多问题）/ backtrack（模糊）/ adaptive（自适应）
3. sub_queries: 1-2 个可直接检索的子问题（当 strategy 为 subquery 时）

仅输出 JSON 格式：
{
  "query_type": "...",
  "strategy": "...",
  "sub_queries": ["...", "..."]
}

iteration: 当前是第几次检索迭代（从 0 开始），用于判断是否需要继续迭代。"""

PLAN_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", PLAN_SYSTEM),
        ("human", "查询：{query}\n当前迭代：{iteration}"),
    ]
)

EVALUATE_SYSTEM = """你是一个质量评估器。评估 retrieved documents 中是否有足够的信息来回答 query。

评估维度（1-1 分制）：
- 相关性：文档内容是否直接回答 query 中的问题？
- 完整性：是否有足够的信息支撑完整回答？
- 准确性：文档是否有明确来源？

输出 JSON：
{
  "confidence": 0.0-1.0,
  "reason": "简要说明"
}"""

EVALUATE_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", EVALUATE_SYSTEM),
        ("human", "用户查询：{query}\n\n检索到的文档：\n{docs}"),
    ]
)

SELF_CRITIQUE_SYSTEM = """你是一个答案自评专家。评估当前答案的质量：

- 如果答案充分且置信度高 → 输出 action: "accept"
- 如果答案信息不足但可以重新检索 → 输出 action: "retry" 并生成新的 sub_queries
- 如果涉及隐私、安全、或超出知识库范围 → 输出 action: "escalate_human"
- 如果答案明显错误或与文档矛盾 → 输出 action: "retry" 并修正检索方向

输出 JSON：
{
  "action": "accept" | "retry" | "escalate_human",
  "reason": "...",
  "new_queries": ["..."]  // 仅 action 为 retry 时需要
}"""

SELF_CRITIQUE_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SELF_CRITIQUE_SYSTEM),
        ("human", "用户查询：{query}\n\n当前答案：\n{answer}\n\n置信度：{confidence}"),
    ]
)

SYNTHESIZE_SYSTEM = """你是一个专业的教育领域问答助手。基于检索到的文档回答用户问题。

要求：
- 严格基于检索结果
- 引用来源编号，如 [Source 1]、[Source 2]
- 结构清晰，使用有序列表或代码块
- 如果检索结果不足，诚实告知
- 置信度低于 0.5 时在答案末尾注明此提醒"""

SYNTHESIZE_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYNTHESIZE_SYSTEM),
        (
            "human",
            "用户查询：{query}\n\n检索到的文档：\n{context}\n\n置信度：{confidence}",
        ),
    ]
)

HUMAN_ESCALATION_SYSTEM = """由于答案置信度不足或涉及敏感内容，需要人工审核。

请提供以下信息：
- 原始查询
- 已尝试的检索策略
- 检索到的文档摘要
- 当前答案（如有）
- 建议人工介入的原因"""

HUMAN_ESCALATION_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", HUMAN_ESCALATION_SYSTEM),
        ("human", "查询：{query}\n当前答案：{answer}"),
    ]
)
