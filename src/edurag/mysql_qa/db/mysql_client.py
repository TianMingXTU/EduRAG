import asyncio
from datetime import datetime
from tortoise import Tortoise, fields
from edurag.mysql_qa.db.models import FQAQAPair
from edurag.base.config import config
from edurag.base.logger import logger


class MysqlClient:
    def __init__(self):
        self._instance = False

    async def init_db(self):
        """初始化mysql"""
        try:
            if self._instance == False:
                db_url = f"mysql://{config.db_user}:{config.db_password}@{config.db_localhost}:{config.db_port}/{config.db_database}?charset=utf8mb4"
                await Tortoise.init(
                    db_url=db_url,
                    modules={"models": ["edurag.mysql_qa.db.models"]},
                )

                await Tortoise.generate_schemas()
                logger.info("init_db sucessed")
                self._instance = True
        except Exception as e:
            logger.error(f"init_db error : {e}")

    async def close(self):
        if self._instance:
            await Tortoise.close_connections()
            self._instance = False

    async def query_all_fqa(self):
        await self.init_db()
        qs = await FQAQAPair.filter(is_active=True).values(
            "id", "question", "answer", "subject", "tags", "question_tokens", "priority"
        )
        return list(qs)

    async def get_answer_by_question(self, question):
        await self.init_db()
        obj = await FQAQAPair.filter(question=question, is_active=True).first()
        return obj.answer if obj else None


async def main():
    # 1. 实例化你的 MySQL 客户端
    db_client = MysqlClient()

    try:
        # 2. 初始化数据库连接
        await db_client.init_db()

        # 3. 测试调用：查询所有活跃的 FQA 列表
        logger.info("--- 开始查询所有 FQA 数据 ---")
        fqa_list = await db_client.query_all_fqa()
        logger.info(f"查询成功，共获取到 {len(fqa_list)} 条记录")
        for item in fqa_list[:3]:  # 打印前 3 条测试
            print(item)

        # 4. 测试调用：根据问题精确匹配答案
        test_question = "什么是 Python 中的 GIL（全局解释器锁）？"  # 替换为你数据库里实际有的问题进行测试
        logger.info(f"--- 开始查询问题: '{test_question}' ---")
        answer = await db_client.get_answer_by_question(test_question)
        print(f"查询结果: {answer}")

    except Exception as e:
        logger.error(f"main 执行过程中发生错误: {e}")
    finally:
        # 5. 确保在程序退出前关闭 Tortoise 的数据库连接池
        await db_client.close()
        logger.info("数据库连接已安全关闭")


if __name__ == "__main__":
    # 使用 asyncio 启动异步主函数
    asyncio.run(main())
