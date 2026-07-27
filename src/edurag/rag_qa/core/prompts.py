from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

QUERY_CLASSIFIER_SYSTEM = (
    "你是一个查询分类器。判断用户问题是「通用知识」还是「专业咨询」。\n\n"
    "通用知识：日常聊天、问候、通用常识、无需检索内部知识库即可回答的问题。\n"
    "专业咨询：需要查询教培机构内部知识库才能回答的技术问题、课程问题、政策问题。\n\n"
    "仅输出一个词：general_knowledge 或 professional_consultation。"
)

query_classifier_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", QUERY_CLASSIFIER_SYSTEM),
        ("human", "{query}"),
    ]
)

STRATEGY_SELECTOR_SYSTEM = (
    "你是一个 RAG 检索策略选择器。根据用户问题选择最佳检索策略。\n\n"
    "可选策略及适用场景：\n"
    "1. direct — 问题明确、具体、关键词清晰。直接用原问题检索。\n"
    "2. hyde — 问题抽象、概念性、用户想了解某个主题但表述笼统。需先生成假设答案再检索。\n"
    "3. subquery — 问题复杂、包含多个子问题、需要对比。需拆解为多个子问题分别检索。\n"
    "4. backtrack — 问题模糊、指代不清、包含冗余信息。需提取核心意图再检索。\n\n"
    "仅输出策略名称：direct / hyde / subquery / backtrack"
)

strategy_selector_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", STRATEGY_SELECTOR_SYSTEM),
        ("human", "{query}"),
    ]
)

HYDE_SYSTEM = (
    "你是一个假设答案生成器。用户的问题比较抽象或笼统，"
    "请根据你对教培领域知识的理解，生成一段尽可能详细的假设性回答。\n\n"
    "要求：\n"
    "- 包含可能涉及的核心概念、技术术语、步骤名称\n"
    "- 结构清晰，按逻辑组织\n"
    "- 此答案仅用于检索，不需要 100% 准确\n"
    "- 不要提及假设或可能等字眼，直接写答案本身"
)

hyde_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", HYDE_SYSTEM),
        ("human", "{query}"),
    ]
)

SUBQUERY_SYSTEM = (
    "你是一个问题分解器。用户问题包含多个方面，需要拆解为独立的子问题。\n"
    "输出格式：每行一个子问题，不要编号，不要额外文字。\n"
    "每个子问题应当是独立的、可直接检索的完整问句。"
)

subquery_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SUBQUERY_SYSTEM),
        ("human", "{query}"),
    ]
)

BACKTRACK_SYSTEM = (
    "你是一个核心意图提取器。用户的问题模糊、冗余或有指代不清的内容。\n"
    "请忽略修饰性语言和指代词，提取出最核心的检索意图。\n"
    "仅输出一句话的核心检索词/关键词组合。"
)

backtrack_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", BACKTRACK_SYSTEM),
        ("human", "{query}"),
    ]
)

ANSWER_SYNTHESIS_SYSTEM = (
    "你是一个专业的教育培训领域答疑助手。基于以下检索到的知识片段回答用户问题。\n\n"
    "要求：\n"
    "- 严格基于检索结果，不添加未经证实的内容\n"
    "- 如果检索结果不足，诚实告知未找到相关信息\n"
    "- 引用来源时标注文档片段的关键内容\n"
    "- 回答结构清晰，使用适当的分点和格式\n"
    "- 如果涉及代码，用代码块包裹"
)

answer_synthesis_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", ANSWER_SYNTHESIS_SYSTEM),
        ("human", "检索到的知识片段：\n{context}\n\n用户问题：{query}"),
    ]
)
