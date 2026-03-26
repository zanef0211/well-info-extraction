"""
API测试接口 - 用于本地测试
"""
import logging
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException

from api.routes import get_pipeline
from api.schemas import ProcessingResponse, BatchProcessingResponse

from utils.logger import get_logger

logger = get_logger(__name__)

# 创建测试路由器
test_router = APIRouter(prefix="/test", tags=["测试"])


@test_router.get("/status")
async def test_status():
    """测试接口状态"""
    return {
        "status": "ok",
        "message": "测试接口可用",
    }


@test_router.get("/pipeline")
async def test_pipeline():
    """测试处理管道是否初始化"""
    try:
        pipeline = get_pipeline()
        return {
            "status": "ok",
            "pipeline_initialized": pipeline is not None,
        }
    except HTTPException as e:
        return {
            "status": "error",
            "message": e.detail,
        }


@test_router.post("/process/demo")
async def test_process_demo():
    """
    测试处理功能(使用示例文件)
    """
    try:
        pipeline = get_pipeline()

        # 查找测试文件
        demo_file = Path("tests/demo/sample.pdf")
        if not demo_file.exists():
            # 尝试其他路径
            demo_file = Path("storage/uploads/sample.pdf")
            if not demo_file.exists():
                raise HTTPException(
                    status_code=404,
                    detail="测试文件不存在,请先上传测试文件"
                )

        logger.info(f"使用测试文件: {demo_file}")

        # 处理文件
        result = pipeline.run(file_path=str(demo_file))

        return ProcessingResponse(
            success=True,
            message="测试处理成功",
            data=result.to_dict(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"测试处理失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"测试处理失败: {str(e)}")


@test_router.get("/storage/files")
async def list_storage_files():
    """列出存储目录中的文件"""
    try:
        upload_dir = Path("storage/uploads")
        if not upload_dir.exists():
            return {"files": []}

        files = []
        for file_path in upload_dir.rglob("*"):
            if file_path.is_file():
                files.append({
                    "name": file_path.name,
                    "path": str(file_path.relative_to(upload_dir)),
                    "size": file_path.stat().st_size,
                })

        return {
            "total": len(files),
            "files": files[:50],  # 最多返回50个
        }

    except Exception as e:
        logger.error(f"列出文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"列出文件失败: {str(e)}")
