"""
FastAPI应用主文件
"""
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from utils.logger import get_logger
from api.routes import router

logger = get_logger(__name__)

# 全局变量,用于存储处理管道实例
pipeline_instance = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global pipeline_instance

    # 启动时初始化
    logger.info("=" * 50)
    logger.info("AI驱动油气井关键信息提取服务启动")
    logger.info("=" * 50)

    try:
        # 初始化处理管道
        from pipeline.pipeline import ProcessingPipeline
        from models.ocr_engine import OCREngine
        from models.llm_client import LLMClientFactory

        # 初始化OCR引擎
        ocr_engine = OCREngine(
            use_angle_cls=True,
            lang="ch",
            use_gpu=settings.OCR_USE_GPU,
        )

        # 初始化LLM客户端
        llm_client = LLMClientFactory.create_client(
            provider="qwen",  # 使用 Qwen 提供商（兼容 DashScope）
            api_key=settings.LLM_API_KEY,
            model=settings.LLM_MODEL_EXTRACT,  # 使用提取模型
            temperature=0.1,
        )

        # 创建处理管道
        pipeline_instance = ProcessingPipeline(
            ocr_engine=ocr_engine,
            llm_client=llm_client,
            enhance_images=True,
            clean_text=True,
        )

        logger.info("处理管道初始化成功")

        # 检查存储目录
        storage_dirs = [
            settings.UPLOAD_DIR,
            settings.PROCESSED_DIR,
            settings.CACHE_DIR,
        ]
        for dir_path in storage_dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            logger.info(f"存储目录已创建: {dir_path}")

    except Exception as e:
        logger.error(f"初始化失败: {e}", exc_info=True)
        raise

    yield

    # 关闭时清理
    logger.info("服务关闭中...")
    pipeline_instance = None
    logger.info("服务已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="AI驱动油气井关键信息提取API",
    description="基于AI的油气井文档关键信息自动提取服务",
    version="1.0.0",
    lifespan=lifespan,
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.API_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 注册路由
app.include_router(router, prefix=settings.API_PREFIX, tags=["处理"])


@app.get("/", tags=["系统"])
async def root():
    """根路径"""
    return {
        "message": "AI驱动油气井关键信息提取API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查"""
    # 检查处理管道是否初始化
    models_loaded = {
        "ocr": pipeline_instance is not None,
        "llm": pipeline_instance is not None,
    }

    # 检查存储
    storage_available = Path(settings.UPLOAD_DIR).exists()

    return {
        "status": "healthy" if pipeline_instance else "initializing",
        "version": "1.0.0",
        "models_loaded": models_loaded,
        "storage_available": storage_available,
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """通用异常处理"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": f"服务器内部错误: {str(exc)}",
            "timestamp": datetime.now().isoformat(),
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.app:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
