from rank_bm25 import BM25Okapi

# 1. 准备语料库（3 篇经过分词的文档）
corpus = [
    ["python", "编程", "入门", "基础"],  # 文档 0
    ["java", "并发", "编程", "实战"],  # 文档 1
    ["深度", "学习", "python", "ai", "应用"],  # 文档 2
]

# 2. 初始化 BM25 实例
bm25 = BM25Okapi(corpus)

# 3. 准备用户查询词 (Query)
tokens = ["python", "编程", "入门", "基础"]

# 4. 调用 API 计算得分
scores = bm25.get_scores(tokens)

print(scores)
# 输出可能类似于：array([0.4851, 0.0, 1.2541])
best_idx = scores.argmax()
print(best_idx)
best_score = float(scores[best_idx])
print(best_score)
best_item = corpus[best_idx]
print(best_item)
