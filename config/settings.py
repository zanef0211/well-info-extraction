"""全局配置"""
import os
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    # ========== 应用配置 ==========
    APP_NAME: str = "WellInfo Extractor"
    APP_VERSION: str = "v1.0.0"
    DEBUG: bool = True  # 启用调试模式

    # ========== LLM 配置 ==========
    LLM_API_KEY: str
    LLM_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    LLM_MODEL_CLASSIFY: str = "qwen2.5-14b-instruct"
    LLM_MODEL_EXTRACT: str = "qwen2.5-72b-instruct"
    LLM_MODEL_WELLNO: str = "qwen2.5-7b-instruct"
    LLM_TEMPERATURE: float = 0.05
    LLM_MAX_TOKENS: int = 4096
    LLM_TIMEOUT: int = 120

    # ========== OCR 配置 ==========
    OCR_USE_GPU: bool = False
    OCR_LANG: str = "ch"
    OCR_DROP_SCORE: float = 0.5

    # ========== 数据库配置 ==========
    DATABASE_URL: str = "postgresql://wellinfo:wellinfo123@localhost:5432/wellinfo"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # ========== Redis 配置 ==========
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_TTL: int = 3600  # 缓存过期时间 (秒)
    REDIS_MAX_CONNECTIONS: int = 10

    # ========== 存储配置 ==========
    STORAGE_PATH: str = "./storage"
    UPLOAD_DIR: str = "./storage/uploads"
    PROCESSED_DIR: str = "./storage/processed"
    CACHE_DIR: str = "./storage/cache"

    # ========== API 配置 ==========
    API_PREFIX: str = "/api/v1"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    BATCH_MAX_FILES: int = 100
    API_CORS_ORIGINS: list = ["*"]  # CORS 允许的来源

    # ========== JWT 配置 ==========
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24小时

    # ========== 限流配置 ==========
    RATE_LIMIT_PER_USER: int = 10  # 每秒请求数

    # ========== 批量处理配置 ==========
    BATCH_MAX_WORKERS: int = 4
    BATCH_TIMEOUT_SECONDS: int = 120

    # ========== 校验配置 ==========
    CONFIDENCE_THRESHOLD: float = 0.70  # 自动入库阈值


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


# 导出全局配置实例
settings = get_settings()
