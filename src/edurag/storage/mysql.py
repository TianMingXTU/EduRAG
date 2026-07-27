from tortoise import Tortoise
from edurag.config import settings
from edurag.config.logging import logger


class DatabaseManager:
    _initialized: bool = False

    @classmethod
    async def init(cls) -> None:
        if cls._initialized:
            return
        await Tortoise.init(
            db_url=settings.mysql_dsn,
            modules={"models": ["edurag.mysql_qa.db.models"]},
        )
        await Tortoise.generate_schemas()
        cls._initialized = True
        logger.info("Database initialized")

    @classmethod
    async def close(cls) -> None:
        if cls._initialized:
            await Tortoise.close_connections()
            cls._initialized = False
            logger.info("Database closed")

    @classmethod
    async def ensure(cls) -> None:
        if not cls._initialized:
            await cls.init()


mysql_client = DatabaseManager()
