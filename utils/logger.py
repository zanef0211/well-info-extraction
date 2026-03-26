"""日志工具"""
import sys
from loguru import logger
from config.settings import get_settings

settings = get_settings()

# 配置日志
logger.remove()  # 移除默认的处理器

# 控制台输出
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO" if not settings.DEBUG else "DEBUG",
    colorize=True,
)

# 文件输出
logger.add(
    "logs/app_{time:YYYY-MM-DD}.log",
    rotation="00:00",  # 每天轮换
    retention="30 days",  # 保留30天
    compression="zip",  # 压缩旧日志
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG" if settings.DEBUG else "INFO",
)

# 错误日志单独输出
logger.add(
    "logs/error_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="30 days",
    compression="zip",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="ERROR",
)


def get_logger(name: str = None):
    """获取logger实例"""
    if name:
        return logger.bind(name=name)
    return logger
