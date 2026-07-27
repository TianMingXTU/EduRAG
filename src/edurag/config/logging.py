import sys
from pathlib import Path
from loguru import logger

LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logger.remove()

LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

logger.add(
    sink=sys.stdout,
    format=LOG_FORMAT,
    level="INFO",
    colorize=True,
)

logger.add(
    sink=LOG_DIR / "app_{time:YYYY-MM-DD}.log",
    format=LOG_FORMAT,
    level="DEBUG",
    rotation="00:00",
    retention="30 days",
    compression="zip",
    encoding="utf-8",
    enqueue=True,
)

logger.add(
    sink=LOG_DIR / "error_{time:YYYY-MM-DD}.log",
    format=LOG_FORMAT,
    level="ERROR",
    rotation="10 MB",
    retention="60 days",
    encoding="utf-8",
    enqueue=True,
    backtrace=True,
    diagnose=True,
)

__all__ = ["logger"]
