"""插入模拟 FQA 数据，运行：python seed_data.py"""

import asyncio
import jieba
from tortoise import Tortoise
from edurag.mysql_qa.db.models import FQAQAPair

MOCK_DATA = [
    {
        "question": "什么是 Python 中的 GIL（全局解释器锁）？",
        "answer": "GIL（Global Interpreter Lock，全局解释器锁）是 CPython 解释器中的一个互斥锁，它确保同一时刻只有一个线程执行 Python 字节码。GIL 简化了内存管理，但限制了多线程并行执行 CPU 密集型任务。对于 I/O 密集型任务，GIL 影响较小；对于 CPU 密集型任务，建议使用多进程（multiprocessing）替代多线程。",
        "subject": "python",
    },
    {
        "question": "Python 中列表和元组的区别是什么？",
        "answer": "1. 可变性：列表可变，元组不可变\n2. 语法：列表用 []，元组用 ()\n3. 性能：元组创建和访问更快\n4. 用途：列表存同类数据，元组存异构数据\n5. 哈希：元组可哈希（元素可哈希时），列表不可哈希",
        "subject": "python",
    },
    {
        "question": "什么是 Python 装饰器？",
        "answer": "装饰器是一个高阶函数，接收一个函数作为参数，返回一个新函数，用于在不修改原函数代码的情况下扩展其功能。常见用途：日志记录、性能计时、权限校验、缓存。使用 @ 语法糖：@decorator def func(): pass。",
        "subject": "python",
    },
    {
        "question": "Python 中 __init__ 和 __call__ 的区别？",
        "answer": "__init__ 是构造函数，在创建实例时自动调用，用于初始化实例属性。__call__ 使实例对象可像函数一样被调用，在 obj() 时触发。一个是创建时调用，一个是调用时触发。",
        "subject": "python",
    },
    {
        "question": "Python 生成器和迭代器的区别？",
        "answer": "迭代器是实现了 __iter__ 和 __next__ 方法的对象。生成器是含有 yield 关键字的函数，每次调用 yield 暂停执行并返回值，next() 恢复执行。生成器是创建迭代器的最简方式，节省内存。",
        "subject": "python",
    },
    {
        "question": "Java 中 HashMap 和 ConcurrentHashMap 的区别？",
        "answer": "HashMap：线程不安全，允许 null key/value，JDK 1.2 引入，通过数组+链表+红黑树实现。ConcurrentHashMap：线程安全，不允许 null key/value，JDK 1.5 引入，分段锁/CAS+synchronized 实现，适合高并发场景。",
        "subject": "java",
    },
    {
        "question": "Java 抽象类和接口的区别？",
        "answer": "1. 构造方法：抽象类有，接口无\n2. 成员变量：抽象类任意，接口只能 public static final\n3. 方法：抽象类有抽象+具体方法，接口默认方法+静态方法（JDK 8+）\n4. 继承：单继承抽象类，多实现接口\n5. 设计目的：抽象类表达 is-a 关系，接口表达 can-do 能力",
        "subject": "java",
    },
    {
        "question": "Java 中 volatile 关键字的作用？",
        "answer": "volatile 保证多线程间的可见性：一个线程修改 volatile 变量后，其他线程立即看到最新值。禁止指令重排序。不保证原子性（如需原子性，使用 synchronized 或 Atomic 类）。比 synchronized 轻量，适合状态标志位场景。",
        "subject": "java",
    },
    {
        "question": "Java 8 的 Stream API 中 map 和 flatMap 的区别？",
        "answer": "map：一对一转换，每个元素映射为一个新元素，结果流长度不变。flatMap：一对多转换，每个元素映射为多个元素，结果流被展平（扁平化）为单个流。",
        "subject": "java",
    },
    {
        "question": "什么是 JVM 的垃圾回收机制？",
        "answer": "JVM 自动管理内存，通过 GC 回收不再使用的对象。主要算法：标记-清除、标记-复制、标记-整理。分代回收：新生代（Minor GC，复制算法）、老年代（Major GC，标记-整理）。常用 GC 器：Serial、Parallel、CMS、G1、ZGC。",
        "subject": "java",
    },
    {
        "question": "MySQL 中什么是索引？有哪些类型？",
        "answer": "索引是帮助 MySQL 高效获取数据的数据结构。类型：B+Tree 索引（最常用）、Hash 索引、全文索引、空间索引。从逻辑分：主键索引（唯一且非空）、唯一索引、普通索引、联合索引（最左匹配原则）、全文索引。",
        "subject": "ops",
    },
    {
        "question": "MySQL 事务 ACID 是什么？",
        "answer": "A（Atomicity）原子性：事务要么全部成功要么全部回滚。C（Consistency）一致性：事务前后数据满足所有约束。I（Isolation）隔离性：并发事务互不干扰。D（Durability）持久性：提交后数据永久保存。InnoDB 通过 undo log、redo log、锁机制实现 ACID。",
        "subject": "ops",
    },
    {
        "question": "Docker 和虚拟机的区别？",
        "answer": "Docker 是操作系统级虚拟化，共享宿主机内核，启动秒级，镜像大小 MB 级。虚拟机是硬件级虚拟化，包含完整操作系统，启动分钟级，大小 GB 级。Docker 资源利用率更高，但隔离性弱于虚拟机。",
        "subject": "ops",
    },
    {
        "question": "Linux 中如何查看进程占用端口？",
        "answer": "常用命令：\n1. lsof -i :端口号（需 root 或该进程所有者）\n2. netstat -tlnp | grep 端口号\n3. ss -tlnp | grep 端口号（推荐，性能更好）",
        "subject": "ops",
    },
    {
        "question": "Hadoop 和 Spark 的区别？",
        "answer": "Hadoop：MapReduce 计算模型，数据 Shuffle 到磁盘，适合批处理，速度慢。Spark：基于内存计算，DAG 调度，适合迭代计算和实时处理，速度可比 Hadoop 快 10-100 倍。Spark 可运行在 Hadoop YARN 上，读取 HDFS 数据。",
        "subject": "bigdata",
    },
    {
        "question": "HBase 中 RowKey 设计原则？",
        "answer": "1. 长度原则：越短越好，不超过 16KB\n2. 散列原则：通过加盐/哈希避免热点\n3. 唯一原则：RowKey 唯一标识一行\n4. 排序原则：利用 HBase 字典序存储，将一起查询的数据放在相邻 RowKey\n5. 反转原则：时间戳反转使最新数据在前",
        "subject": "bigdata",
    },
    {
        "question": "Kafka 中消息丢失怎么解决？",
        "answer": "生产者端：acks=all（等待所有副本确认），重试次数合理设置，开启幂等性（enable.idempotence=true）。Broker 端：min.insync.replicas >= 2， unclean.leader.election.enable=false。消费者端：手动提交 offset，处理完再提交。",
        "subject": "bigdata",
    },
    {
        "question": "机器学习中过拟合怎么解决？",
        "answer": "1. 增加训练数据量\n2. 减少模型复杂度（降低层数/特征数）\n3. 正则化（L1/L2）\n4. Dropout（随机丢弃神经元）\n5. 早停（Early Stopping）\n6. 数据增强\n7. 交叉验证",
        "subject": "ai",
    },
    {
        "question": "什么是激活函数？常见的有哪些？",
        "answer": "激活函数引入非线性，使神经网络能学习复杂模式。常见激活函数：\nSigmoid：输出(0,1)，适合二分类输出层，易梯度消失\nTanh：输出(-1,1)，零中心，仍有梯度消失\nReLU：输出 max(0,x)，计算快，缓解梯度消失，但存在神经元死亡\nLeaky ReLU / ELU / GELU 是 ReLU 的改进版本。",
        "subject": "ai",
    },
    {
        "question": "什么是 Transformer 的自注意力机制？",
        "answer": "自注意力计算 Q（Query）、K（Key）、V（Value）三个矩阵，通过 Q·K^T 计算注意力分数，softmax 归一化后加权聚合 V。公式：Attention(Q,K,V) = softmax(QK^T/√d_k)V。优势：全局感知、可并行、长距离依赖优于 RNN。",
        "subject": "ai",
    },
    {
        "question": "什么是 HTTPS 和 SSL/TLS？",
        "answer": "HTTPS = HTTP + SSL/TLS，在 HTTP 下加了一层加密协议。TLS 握手过程：\n1. Client Hello（告知支持的加密套件）\n2. Server Hello（选择加密套件，下发证书）\n3. 客户端验证证书\n4. 交换密钥（RSA 或 ECDHE）\n5. 开始加密通信\n端口 443。",
        "subject": "ai",
    },
    {
        "question": "Python 中深拷贝和浅拷贝的区别？",
        "answer": "浅拷贝（copy.copy）：创建新对象，但嵌套对象引用原对象的内存地址。深拷贝（copy.deepcopy）：递归复制所有对象，完全独立。赋值（=）不创建副本，只是增加引用。对于不可变类型，浅拷贝和深拷贝效果相同。修改嵌套可变对象时差异明显。",
        "subject": "python",
    },
    {
        "question": "MySQL 中 JOIN 的几种类型？",
        "answer": "1. INNER JOIN：只返回匹配的行\n2. LEFT JOIN：返回左表所有行，右表无匹配填 NULL\n3. RIGHT JOIN：返回右表所有行，左表无匹配填 NULL\n4. FULL OUTER JOIN：返回两表所有行（MySQL 不支持，用 UNION 模拟）\n5. CROSS JOIN：笛卡尔积",
        "subject": "ops",
    },
    {
        "question": "什么是 RESTful API 设计原则？",
        "answer": "1. 资源导向：URL 表示资源，而非操作\n2. 使用标准 HTTP 方法：GET（查）、POST（增）、PUT（全量改）、PATCH（部分改）、DELETE（删）\n3. 无状态：每次请求包含全部信息\n4. 统一接口\n5. 使用 JSON 或 XML\n6. 版本控制：/v1/resource",
        "subject": "general",
    },
    {
        "question": "Git 中 rebase 和 merge 的区别？",
        "answer": "merge：创建一个新的合并提交，保留完整的分支历史，适合公共分支。rebase：将当前分支的提交在目标分支顶部重放，历史线性整洁，适合个人分支。rebase 后需要强制推送（force push），不要在公共分支上 rebase。黄金法则：不要 rebase 别人已经拉取的分支。",
        "subject": "general",
    },
]


async def seed():
    db_url = "mysql://root:Qin2002.@localhost:3306/edu_rag?charset=utf8mb4"
    await Tortoise.init(
        db_url=db_url, modules={"models": ["edurag.mysql_qa.db.models"]}
    )
    await Tortoise.generate_schemas()

    existing = await FQAQAPair.all().count()
    if existing > 0:
        print(f"表中已有 {existing} 条数据，跳过插入。如需重新插入，请先 truncate 表。")
        return

    for item in MOCK_DATA:
        tokens = list(jieba.cut(item["question"]))
        await FQAQAPair.create(
            question=item["question"],
            answer=item["answer"],
            subject=item["subject"],
            tags=[],
            question_tokens=tokens,
            is_active=True,
            priority=1,
        )
        print(f"  ✔ {item['question'][:30]}...")

    total = await FQAQAPair.all().count()
    print(f"\n插入完成，共 {total} 条数据。")


if __name__ == "__main__":
    asyncio.run(seed())
