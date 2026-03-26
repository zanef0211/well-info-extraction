"""
程序主入口
"""
import uvicorn
from api.app import app
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("AI驱动油气井关键信息提取服务")
    logger.info("=" * 60)
    logger.info(f"版本: 1.0.0")
    logger.info(f"API地址: http://{settings.API_HOST}:{settings.API_PORT}")
    logger.info(f"API文档: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    logger.info(f"调试模式: {settings.DEBUG}")
    logger.info("=" * 60)

    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    main()
