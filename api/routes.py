"""
API路由定义
"""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends

from config.settings import settings
from preprocess.file_handler import FileHandler
from validation.field_validator import FieldValidator
from validation.data_quality_checker import DataQualityChecker
from api.schemas import (
    ProcessRequest,
    BatchProcessRequest,
    SingleWellBatchRequest,
    ValidateRequest,
    QualityCheckRequest,
    ProcessingResponse,
    BatchProcessingResponse,
    SingleWellBatchResponse,
    ValidationResponse,
    ValidationSummaryResponse,
    QualityReportResponse,
)

from utils.logger import get_logger

logger = get_logger(__name__)

# 创建路由器
router = APIRouter()

# 获取处理管道实例的依赖项
def get_pipeline():
    """获取处理管道实例"""
    from api.app import pipeline_instance
    if pipeline_instance is None:
        raise HTTPException(status_code=503, detail="服务正在初始化,请稍后重试")
    return pipeline_instance


# ========== 处理接口 ==========

@router.post("/extract/single", response_model=ProcessingResponse)
async def extract_single_document(
    file: UploadFile = File(..., description="上传的文件"),
    target_fields: Optional[str] = Form(None, description="目标字段列表(JSON数组字符串)"),
    category: Optional[str] = Form(None, description="一级分类"),
    doc_category: Optional[str] = Form(None, description="二级文档分类"),
    enhance_images: bool = Form(True, description="是否增强图像"),
    clean_text: bool = Form(True, description="是否清洗文本"),
    pipeline = Depends(get_pipeline),
):
    """
    单文档信息提取

    场景1: 单口井单个文档处理

    功能: 上传单个文档,返回结构化抽取结果
    """
    try:
        if not request.file_path:
            raise HTTPException(status_code=400, detail="必须提供文件路径")

        # 检查文件是否存在
        if not Path(request.file_path).exists():
            raise HTTPException(status_code=404, detail="文件不存在")

        logger.info(f"开始处理文件: {request.file_path}")

        # 处理文件
        result = pipeline.run(
            file_path=request.file_path,
            document_id=request.document_id,
            target_fields=request.target_fields,
        )

        return ProcessingResponse(
            success=True,
            message="文件处理成功",
            data=result.to_dict(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件处理失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")


@router.post("/process/upload", response_model=ProcessingResponse)
async def process_uploaded_file(
    file: UploadFile = File(..., description="上传的文件"),
    target_fields: str = Form(None, description="目标字段列表(JSON数组字符串)"),
    enhance_images: bool = Form(True, description="是否增强图像"),
    clean_text: bool = Form(True, description="是否清洗文本"),
    pipeline = Depends(get_pipeline),
):
    """
    处理上传的文件
    """
    import json

    try:
        # 验证文件类型
        file_ext = Path(file.filename).suffix.lower()
        allowed_extensions = {
            ".pdf",
            ".docx", ".doc",
            ".xlsx", ".xls",
            ".txt",
            ".jpg", ".jpeg", ".png", ".bmp", ".tiff"
        }
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file_ext}, 支持的类型: {', '.join(allowed_extensions)}"
            )

        # 解析目标字段
        target_fields_list = None
        if target_fields:
            try:
                target_fields_list = json.loads(target_fields)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="target_fields格式错误,应为JSON数组")

        logger.info(f"开始处理上传的文件: {file.filename}")

        # 保存上传的文件
        file_handler = FileHandler(
            upload_dir=settings.STORAGE_UPLOAD_DIR,
            processed_dir=settings.STORAGE_PROCESSED_DIR,
        )

        # 读取文件数据
        file_data = await file.read()

        # 验证文件大小
        if len(file_data) > 100 * 1024 * 1024:  # 100MB
            raise HTTPException(status_code=400, detail="文件大小超过限制(100MB)")

        # 保存文件
        save_result = file_handler.save_uploaded_file(
            file_data=file_data,
            filename=file.filename,
        )

        logger.info(f"文件已保存: {save_result['file_path']}")

        # 处理文件
        result = pipeline.run(
            file_path=save_result["file_path"],
            target_fields=target_fields_list,
        )

        return ProcessingResponse(
            success=True,
            message="文件处理成功",
            data=result.to_dict(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传文件处理失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.post("/process/batch", response_model=BatchProcessingResponse)
async def process_batch_files(
    request: BatchProcessRequest,
    pipeline = Depends(get_pipeline),
):
    """
    批量处理文件
    """
    try:
        if not request.file_paths:
            raise HTTPException(status_code=400, detail="文件路径列表不能为空")

        logger.info(f"开始批量处理 {len(request.file_paths)} 个文件")

        # 批量处理
        results = pipeline.run_batch(
            file_paths=request.file_paths,
            target_fields=request.target_fields,
        )

        # 构建响应
        data_list = [result.to_dict() for result in results]
        summary = pipeline.get_pipeline_summary(results)

        return BatchProcessingResponse(
            success=True,
            message=f"批量处理完成: {len(results)} 个文件",
            data=data_list,
            summary=summary,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量处理失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"批量处理失败: {str(e)}")


@router.post("/process/batch/group")
async def process_and_group_by_well(
    files: List[UploadFile] = File(...),
    pipeline = Depends(get_pipeline),
):
    """
    批量处理文件并按井号分组

    这个接口是核心功能:
    1. 批量上传文件
    2. 识别每份文件的井号
    3. 按井号分组
    4. 返回按井号组织的文档结构

    返回格式:
    {
        "total_files": 10,
        "unique_wells": 3,
        "unrecognized_files": 1,
        "well_groups": {
            "XX-1-1": [
                {文件1处理结果},
                {文件2处理结果}
            ],
            "XX-1-2": [
                {文件3处理结果}
            ],
            ...
        }
    }
    """
    try:
        logger.info(f"开始批量处理并按井号分组: {len(files)} 个文件")

        results = []
        temp_files = []

        try:
            # 保存并处理所有文件
            for file in files:
                # 保存文件
                file_path, original_name = pipeline.file_handler.save_file(
                    file.file,
                    file.filename
                )
                temp_files.append(file_path)

                # 处理文件
                result = pipeline.process_file(file_path)
                result["original_filename"] = original_name
                results.append(result)

            # 按井号分组
            well_groups = pipeline.group_by_well_no(results)

            # 统计信息
            unique_wells = len(well_groups) - (1 if "未识别" in well_groups else 0)
            unrecognized = len(well_groups.get("未识别", []))

            logger.info(
                f"处理完成: {len(results)} 个文件, "
                f"识别到 {unique_wells} 口井, "
                f"未识别 {unrecognized} 个文件"
            )

            return {
                "total_files": len(results),
                "unique_wells": unique_wells,
                "unrecognized_files": unrecognized,
                "well_groups": well_groups,
                "success": True,
                "message": f"处理完成: {unique_wells} 口井, {len(results)} 份文档"
            }

        finally:
            # 清理临时文件
            for file_path in temp_files:
                try:
                    if Path(file_path).exists():
                        Path(file_path).unlink()
                except:
                    pass

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量处理分组失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"批量处理分组失败: {str(e)}")


# ========== 验证接口 ==========

@router.post("/validate", response_model=List[ValidationResponse])
async def validate_data(request: ValidateRequest):
    """
    验证数据
    """
    try:
        validator = FieldValidator()

        results = validator.validate_batch(
            data=request.data,
            document_type=request.document_type,
        )

        # 转换为响应格式
        responses = []
        for field_name, result in results.items():
            responses.append(ValidationResponse(
                field_name=field_name,
                is_valid=result.is_valid,
                errors=result.errors,
                warnings=result.warnings,
                confidence=result.confidence,
            ))

        return responses

    except Exception as e:
        logger.error(f"数据验证失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"数据验证失败: {str(e)}")


@router.post("/validate/summary", response_model=ValidationSummaryResponse)
async def validate_summary(request: ValidateRequest):
    """
    获取验证摘要
    """
    try:
        validator = FieldValidator()

        results = validator.validate_batch(
            data=request.data,
            document_type=request.document_type,
        )

        summary = validator.get_validation_summary(results)

        return ValidationSummaryResponse(
            total_fields=summary["total_fields"],
            valid_fields=summary["valid_fields"],
            invalid_fields=summary["invalid_fields"],
            total_errors=summary["total_errors"],
            total_warnings=summary["total_warnings"],
            validation_rate=summary["validation_rate"],
            avg_confidence=summary["avg_confidence"],
            problem_fields=summary["problem_fields"],
        )

    except Exception as e:
        logger.error(f"验证摘要获取失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"验证摘要获取失败: {str(e)}")


# ========== 质量检查接口 ==========

@router.post("/quality/check", response_model=QualityReportResponse)
async def check_quality(request: QualityCheckRequest):
    """
    检查数据质量
    """
    try:
        checker = DataQualityChecker()

        report = checker.check_quality(
            document_id=request.document_id,
            extracted_data=request.extracted_data,
            target_fields=request.target_fields,
            metadata=request.metadata,
        )

        return QualityReportResponse(
            document_id=report.document_id,
            metrics=QualityMetricsResponse(
                completeness=report.metrics.completeness,
                accuracy=report.metrics.accuracy,
                consistency=report.metrics.consistency,
                confidence=report.metrics.confidence,
                overall_score=report.metrics.overall_score,
            ),
            issues=report.issues,
            suggestions=report.suggestions,
            validated_at=report.validated_at,
        )

    except Exception as e:
        logger.error(f"质量检查失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"质量检查失败: {str(e)}")


# ========== 辅助查询接口 ==========

@router.get("/query/well/{well_no}")
async def query_by_well_no(well_no: str):
    """
    按井号查询提取信息

    根据井号返回该井的完整信息,包括:
    - 井基本信息
    - 关联的所有文档
    - 提取的字段数据
    - 质量报告
    - 处理日志

    Args:
        well_no: 井号, 如 "XX-1-1"

    Returns:
        {
            "success": true,
            "message": "查询成功",
            "data": {
                "well_info": {...},
                "documents": [...],
                "extracted_fields": [...],
                "quality_reports": [...],
                "processing_logs": [...],
                "summary": {...}
            }
        }
    """
    try:
        from sqlalchemy.orm import Session
        from db.database import get_db
        from db.models import Well, Document, ExtractedData, QualityReport, ProcessingLog
        from sqlalchemy import func

        db = next(get_db())

        # 1. 查询井信息
        well = db.query(Well).filter(Well.well_no == well_no).first()
        if not well:
            raise HTTPException(status_code=404, detail=f"井号不存在: {well_no}")

        # 2. 查询关联的文档
        documents = db.query(Document).filter(Document.well_no == well_no).all()
        document_ids = [doc.id for doc in documents]

        # 3. 查询提取的字段数据
        extracted_fields = db.query(ExtractedData).filter(
            ExtractedData.well_no == well_no
        ).all()

        # 4. 查询质量报告
        quality_reports = db.query(QualityReport).filter(
            QualityReport.well_no == well_no
        ).all()

        # 5. 查询处理日志
        processing_logs = db.query(ProcessingLog).filter(
            ProcessingLog.well_no == well_no
        ).order_by(ProcessingLog.created_at.desc()).limit(100).all()

        # 6. 汇总统计
        summary = {
            "total_documents": len(documents),
            "total_fields": len(extracted_fields),
            "valid_fields": sum(1 for f in extracted_fields if f.is_valid),
            "avg_confidence": float(
                db.query(func.avg(ExtractedData.confidence)).filter(
                    ExtractedData.well_no == well_no
                ).scalar() or 0
            ),
            "avg_quality_score": float(
                db.query(func.avg(QualityReport.overall_score)).filter(
                    QualityReport.well_no == well_no
                ).scalar() or 0
            ) if quality_reports else 0,
            "document_status_counts": {
                "pending": sum(1 for d in documents if d.status == "pending"),
                "processing": sum(1 for d in documents if d.status == "processing"),
                "success": sum(1 for d in documents if d.status == "success"),
                "failed": sum(1 for d in documents if d.status == "failed"),
            }
        }

        # 构建响应
        result = {
            "success": True,
            "message": "查询成功",
            "data": {
                "well_info": {
                    "well_no": well.well_no,
                    "well_name": well.well_name,
                    "oilfield": well.oilfield,
                    "block": well.block,
                    "well_type": well.well_type,
                    "well_pattern": well.well_pattern,
                    "well_class": well.well_class,
                    "latitude": float(well.latitude) if well.latitude else None,
                    "longitude": float(well.longitude) if well.longitude else None,
                    "elevation": float(well.elevation) if well.elevation else None,
                    "ground_elevation": float(well.ground_elevation) if well.ground_elevation else None,
                    "drill_date": well.drill_date.isoformat() if well.drill_date else None,
                    "completion_date": well.completion_date.isoformat() if well.completion_date else None,
                    "status": well.status,
                    "created_at": well.created_at.isoformat() if well.created_at else None,
                    "updated_at": well.updated_at.isoformat() if well.updated_at else None,
                },
                "documents": [
                    {
                        "id": doc.id,
                        "document_id": doc.document_id,
                        "filename": doc.filename,
                        "file_path": doc.file_path,
                        "file_size": doc.file_size,
                        "file_extension": doc.file_extension,
                        "mime_type": doc.mime_type,
                        "document_type": doc.document_type,
                        "category": doc.category,
                        "doc_category": doc.doc_category,
                        "upload_date": doc.upload_date.isoformat() if doc.upload_date else None,
                        "uploaded_by": doc.uploaded_by,
                        "status": doc.status,
                        "created_at": doc.created_at.isoformat() if doc.created_at else None,
                    }
                    for doc in documents
                ],
                "extracted_fields": [
                    {
                        "id": field.id,
                        "document_id": field.document_id,
                        "well_no": field.well_no,
                        "field_name": field.field_name,
                        "field_value": field.field_value,
                        "field_type": field.field_type,
                        "confidence": float(field.confidence) if field.confidence else None,
                        "is_valid": field.is_valid,
                        "validation_errors": field.validation_errors,
                        "source": field.source,
                        "created_at": field.created_at.isoformat() if field.created_at else None,
                    }
                    for field in extracted_fields
                ],
                "quality_reports": [
                    {
                        "id": qr.id,
                        "document_id": qr.document_id,
                        "well_no": qr.well_no,
                        "completeness": float(qr.completeness) if qr.completeness else None,
                        "accuracy": float(qr.accuracy) if qr.accuracy else None,
                        "consistency": float(qr.consistency) if qr.consistency else None,
                        "confidence": float(qr.confidence) if qr.confidence else None,
                        "overall_score": float(qr.overall_score) if qr.overall_score else None,
                        "quality_level": qr.quality_level,
                        "issues": qr.issues,
                        "suggestions": qr.suggestions,
                        "validated_at": qr.validated_at.isoformat() if qr.validated_at else None,
                    }
                    for qr in quality_reports
                ],
                "processing_logs": [
                    {
                        "id": log.id,
                        "document_id": log.document_id,
                        "well_no": log.well_no,
                        "stage": log.stage,
                        "status": log.status,
                        "duration_ms": log.duration_ms,
                        "message": log.message,
                        "error_message": log.error_message,
                        "log_metadata": log.log_metadata,
                        "created_at": log.created_at.isoformat() if log.created_at else None,
                    }
                    for log in processing_logs
                ],
                "summary": summary
            }
        }

        db.close()
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询井信息失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/query/well/{well_no}/fields")
async def query_well_fields(
    well_no: str,
    field_names: str = None,
    include_invalid: bool = False
):
    """
    按井号查询提取的字段

    Args:
        well_no: 井号
        field_names: 可选,字段名称列表(逗号分隔),如 "WellNo,RigModel,TotalDepth"
        include_invalid: 是否包含无效字段,默认False

    Returns:
        {
            "success": true,
            "data": {
                "well_no": "XX-1-1",
                "fields": [
                    {
                        "field_name": "WellNo",
                        "values": [
                            {"value": "XX-1-1", "document_id": 123, "confidence": 0.95}
                        ]
                    },
                    ...
                ]
            }
        }
    """
    try:
        from db.database import get_db
        from db.models import ExtractedData
        from sqlalchemy import and_, or_

        db = next(get_db())

        # 构建查询条件
        query = db.query(ExtractedData).filter(ExtractedData.well_no == well_no)

        # 如果指定了字段名称
        if field_names:
            field_name_list = [f.strip() for f in field_names.split(",")]
            query = query.filter(ExtractedData.field_name.in_(field_name_list))

        # 如果不包含无效字段
        if not include_invalid:
            query = query.filter(ExtractedData.is_valid == True)

        # 查询
        fields = query.all()

        if not fields:
            raise HTTPException(
                status_code=404,
                detail=f"未找到井号 {well_no} 的提取字段"
            )

        # 按字段名分组
        fields_dict = {}
        for field in fields:
            if field.field_name not in fields_dict:
                fields_dict[field.field_name] = []
            fields_dict[field.field_name].append({
                "value": field.field_value,
                "document_id": field.document_id,
                "confidence": float(field.confidence) if field.confidence else None,
                "is_valid": field.is_valid,
                "source": field.source,
                "created_at": field.created_at.isoformat() if field.created_at else None,
            })

        # 按置信度排序
        for field_name in fields_dict:
            fields_dict[field_name].sort(
                key=lambda x: x["confidence"] or 0, reverse=True
            )

        result = {
            "success": True,
            "message": f"查询到 {len(fields_dict)} 个字段",
            "data": {
                "well_no": well_no,
                "total_fields": len(fields_dict),
                "total_values": len(fields),
                "fields": [
                    {
                        "field_name": field_name,
                        "values": values
                    }
                    for field_name, values in fields_dict.items()
                ]
            }
        }

        db.close()
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询井字段失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/query/well/{well_no}/documents")
async def query_well_documents(
    well_no: str,
    category: str = None,
    status: str = None
):
    """
    按井号查询关联的文档

    Args:
        well_no: 井号
        category: 可选,一级分类筛选
        status: 可选,状态筛选

    Returns:
        {
            "success": true,
            "data": {
                "well_no": "XX-1-1",
                "documents": [...],
                "summary": {...}
            }
        }
    """
    try:
        from db.database import get_db
        from db.models import Document, ExtractedData
        from sqlalchemy import func

        db = next(get_db())

        # 构建查询
        query = db.query(Document).filter(Document.well_no == well_no)

        # 分类筛选
        if category:
            query = query.filter(Document.category == category)

        # 状态筛选
        if status:
            query = query.filter(Document.status == status)

        documents = query.all()

        if not documents:
            raise HTTPException(
                status_code=404,
                detail=f"未找到井号 {well_no} 的文档"
            )

        # 汇总统计
        document_ids = [doc.id for doc in documents]
        fields_count = db.query(func.count(ExtractedData.id)).filter(
            ExtractedData.document_id.in_(document_ids)
        ).scalar() or 0

        summary = {
            "total_documents": len(documents),
            "by_category": {},
            "by_status": {},
            "total_fields": fields_count
        }

        # 按分类统计
        for doc in documents:
            if doc.category:
                summary["by_category"][doc.category] = \
                    summary["by_category"].get(doc.category, 0) + 1
            summary["by_status"][doc.status] = \
                summary["by_status"].get(doc.status, 0) + 1

        result = {
            "success": True,
            "message": f"查询到 {len(documents)} 份文档",
            "data": {
                "well_no": well_no,
                "documents": [
                    {
                        "id": doc.id,
                        "document_id": doc.document_id,
                        "filename": doc.filename,
                        "file_path": doc.file_path,
                        "file_size": doc.file_size,
                        "file_extension": doc.file_extension,
                        "document_type": doc.document_type,
                        "category": doc.category,
                        "doc_category": doc.doc_category,
                        "upload_date": doc.upload_date.isoformat() if doc.upload_date else None,
                        "status": doc.status,
                        "created_at": doc.created_at.isoformat() if doc.created_at else None,
                    }
                    for doc in documents
                ],
                "summary": summary
            }
        }

        db.close()
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询井文档失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/query/wells")
async def query_wells_list(
    oilfield: str = None,
    block: str = None,
    well_type: str = None,
    status: str = "active",
    limit: int = 100,
    skip: int = 0
):
    """
    查询井列表

    支持按油田、区块、井别等条件筛选

    Args:
        oilfield: 油田筛选
        block: 区块筛选
        well_type: 井别筛选
        status: 状态筛选,默认active
        limit: 返回数量限制,默认100
        skip: 跳过数量,默认0

    Returns:
        {
            "success": true,
            "data": {
                "total": 10,
                "wells": [...]
            }
        }
    """
    try:
        from db.database import get_db
        from db.models import Well, Document
        from sqlalchemy import func

        db = next(get_db())

        # 构建查询
        query = db.query(Well)

        if oilfield:
            query = query.filter(Well.oilfield == oilfield)
        if block:
            query = query.filter(Well.block == block)
        if well_type:
            query = query.filter(Well.well_type == well_type)
        if status:
            query = query.filter(Well.status == status)

        # 获取总数
        total = query.count()

        # 分页查询
        wells = query.offset(skip).limit(limit).all()

        # 查询每口井的文档数量
        well_nos = [well.well_no for well in wells]
        doc_counts = db.query(
            Document.well_no, func.count(Document.id)
        ).filter(
            Document.well_no.in_(well_nos)
        ).group_by(Document.well_no).all()

        doc_count_dict = {well_no: count for well_no, count in doc_counts}

        result = {
            "success": True,
            "message": f"查询到 {len(wells)} 口井",
            "data": {
                "total": total,
                "limit": limit,
                "skip": skip,
                "wells": [
                    {
                        "well_no": well.well_no,
                        "well_name": well.well_name,
                        "oilfield": well.oilfield,
                        "block": well.block,
                        "well_type": well.well_type,
                        "well_pattern": well.well_pattern,
                        "well_class": well.well_class,
                        "drill_date": well.drill_date.isoformat() if well.drill_date else None,
                        "completion_date": well.completion_date.isoformat() if well.completion_date else None,
                        "status": well.status,
                        "document_count": doc_count_dict.get(well.well_no, 0),
                        "created_at": well.created_at.isoformat() if well.created_at else None,
                    }
                    for well in wells
                ]
            }
        }

        db.close()
        return result

    except Exception as e:
        logger.error(f"查询井列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")
