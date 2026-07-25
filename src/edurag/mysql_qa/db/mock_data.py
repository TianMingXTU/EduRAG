import asyncio
from datetime import datetime
from tortoise import Tortoise, fields
from tortoise.models import Model
from edurag.mysql_qa.db.models import FQAQAPair

MOCK_QA_LIST = [
    {
        "question": "什么是 Python 中的 GIL（全局解释器锁）？",
        "answer": "GIL（Global Interpreter Lock）是 CPython 解释器中的一种机制，确保同一时刻只有一个线程在执行 Python 字节码。这使得 CPython 在多线程环境下无法利用多核 CPU 进行 CPU 密集型计算，但对 IO 密集型任务影响较小。",
        "subject": "python",
        "tags": ["Python", "多线程", "并发", "底层原理"],
        "question_tokens": ["什么", "是", "Python", "中", "的", "GIL", "全局解释器锁"],
        "priority": 10,
    },
    {
        "question": "简述 TCP 三次握手的过程",
        "answer": "TCP 三次握手建立连接过程：\n1. 客户端发送 SYN 包（seq=x）进入 SYN_SENT 状态；\n2. 服务端收到后回复 SYN+ACK 包（seq=y, ack=x+1）进入 SYN_RECV 状态；\n3. 客户端收到后回复 ACK 包（ack=y+1）进入 ESTABLISHED 状态，连接建立。",
        "subject": "network",
        "tags": ["计算机网络", "TCP/IP", "三次握手"],
        "question_tokens": ["简述", "TCP", "三次握手", "的", "过程"],
        "priority": 9,
    },
    {
        "question": "MySQL 中 B+ 树索引相对于 Hash 索引有什么优势？",
        "answer": "1. 支持范围查询与排序：B+ 树叶子节点形成双向链表，极适合 range 查询，而 Hash 索引仅支持等值匹配。\n2. 支持联合索引的最左匹配原则。\n3. 离散度较低时性能更稳定，不会产生 Hash 冲突导致的性能衰减。",
        "subject": "database",
        "tags": ["MySQL", "索引", "B+树", "数据结构"],
        "question_tokens": [
            "MySQL",
            "中",
            "B+树",
            "索引",
            "相对",
            "Hash",
            "索引",
            "优势",
        ],
        "priority": 8,
    },
    {
        "question": "什么是 RAG（检索增强生成）架构？",
        "answer": "RAG（Retrieval-Augmented Generation）通过从外部知识库中检索相关文档/信息作为上下文（Context），与用户 Prompt 一起输入给大语言模型（LLM），从而有效缓解大模型的幻觉问题并提供时效性或私有领域知识。",
        "subject": "ai_rag",
        "tags": ["AI", "RAG", "LLM", "向量检索"],
        "question_tokens": ["什么", "是", "RAG", "检索增强生成", "架构"],
        "priority": 10,
    },
    {
        "question": "Python 中 async/await 的工作原理是什么？",
        "answer": "Python 的 async/await 基于 Event Loop（事件循环）和协程（Coroutine）。当遇到 await 时，当前协程会暂停挂起并交出控制权给事件循环，让事件循环去处理其他已就绪的任务，当异步操作（如网络/磁盘 IO）完成后再唤醒继续执行。",
        "subject": "python",
        "tags": ["Python", "异步编程", "asyncio", "协程"],
        "question_tokens": ["Python", "中", "async", "await", "工作原理"],
        "priority": 7,
    },
]


async def insert_mock_data():
    try:
        # 初始化 Tortoise 数据库连接
        await Tortoise.init(
            db_url="mysql://root:Qin2002.@127.0.0.1:3306/edu_rag?charset=utf8mb4",
            modules={"models": ["edurag.mysql_qa.db.models"]},
        )

        print("开始插入 Mock 数据...")
        inserted_count = 0

        for item in MOCK_QA_LIST:
            # get_or_create 避免重复插入相同问题引发 unique 冲突
            obj, created = await FQAQAPair.get_or_create(
                question=item["question"],
                defaults={
                    "answer": item["answer"],
                    "subject": item["subject"],
                    "tags": item["tags"],
                    "question_tokens": item["question_tokens"],
                    "priority": item["priority"],
                    "is_active": True,
                    "view_count": 0,
                },
            )

            if created:
                inserted_count += 1
                print(f"✅ 成功插入问题: [{item['subject']}] {item['question']}")
            else:
                print(f"⚠️ 问题已存在，跳过: {item['question']}")

        print(f"\n🎉 插入完成！本次新插入 {inserted_count} 条数据。")

        # 查询并打印当前数据库总条数
        total_count = await FQAQAPair.all().count()
        print(f"📊 当前数据库表中的总问答对数据量为: {total_count}")

    finally:
        # 显式关闭连接池，防止 Python 3.14 事件循环退出报错
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(insert_mock_data())
