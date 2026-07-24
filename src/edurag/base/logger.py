import sys
from pathlib import Path
from loguru import logger

# 定义日志保存路径（项目根目录下的 logs 文件夹）
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 1. 移除 loguru 默认的 handler（避免重复打印或格式不统一）
logger.remove()

# 2. 定义统一的日志输出格式
LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

# 3. 添加控制台输出（Console Handler）
logger.add(sink=sys.stdout, format=LOG_FORMAT, level="INFO", colorize=True)

# 4. 添加文件输出 - 普通/详细日志
logger.add(
    sink=LOG_DIR / "app_{time:YYYY-MM-DD}.log",
    format=LOG_FORMAT,
    level="DEBUG",
    rotation="00:00",  # 每天午夜 12 点自动切割
    retention="30 days",  # 保留 30 天日志
    compression="zip",  # 旧日志自动压缩为 zip
    encoding="utf-8",
    enqueue=True,  # 开启线程/进程安全的异步队列写入
)

# 5. 添加文件输出 - 错误日志单独存储
logger.add(
    sink=LOG_DIR / "error_{time:YYYY-MM-DD}.log",
    format=LOG_FORMAT,
    level="ERROR",
    rotation="10 MB",  # 按文件大小切割
    retention="60 days",
    encoding="utf-8",
    enqueue=True,
    backtrace=True,  # 记录完整的异常堆栈
    diagnose=True,  # 变量值诊断（生产环境若含敏感数据可设为 False）
)

# 导出配置好的 logger 对象
__all__ = ["logger"]
