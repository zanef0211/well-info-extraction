"""
处理结果数据结构
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime


@dataclass
class ExtractionResult:
    """提取结果"""
    # 文档信息
    document_id: str
    document_type: str
    document_name: str

    # 提取的数据
    extracted_data: Dict[str, Any]

    # 元数据
    extraction_time: str
    processing_time_ms: float

    # 质量指标
    classification_confidence: float = 0.0
    avg_field_confidence: float = 0.0

    # 验证结果
    validation_errors: List[str] = field(default_factory=list)
    validation_warnings: List[str] = field(default_factory=list)

    # 中间结果(用于调试)
    raw_text: Optional[str] = None
    ocr_results: Optional[List[Dict]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "document_id": self.document_id,
            "document_type": self.document_type,
            "document_name": self.document_name,
            "extracted_data": self.extracted_data,
            "extraction_time": self.extraction_time,
            "processing_time_ms": self.processing_time_ms,
            "classification_confidence": self.classification_confidence,
            "avg_field_confidence": self.avg_field_confidence,
            "validation_errors": self.validation_errors,
            "validation_warnings": self.validation_warnings,
        }


@dataclass
class ProcessingResult:
    """完整处理结果"""
    # 文档信息
    document_id: str
    file_path: str
    original_filename: str

    # 提取结果
    extraction: ExtractionResult

    # 质量评估
    quality_score: float
    completeness: float
    accuracy: float
    consistency: float
    confidence: float

    # 一致性检查
    consistency_errors: List[str] = field(default_factory=list)
    consistency_warnings: List[str] = field(default_factory=list)

    # 规则检查
    rule_errors: List[str] = field(default_factory=list)
    rule_warnings: List[str] = field(default_factory=list)

    # 质量建议
    quality_issues: List[str] = field(default_factory=list)
    quality_suggestions: List[str] = field(default_factory=list)

    # 处理状态
    status: str = "success"  # success, partial, failed
    error_message: Optional[str] = None

    # 处理时间
    total_processing_time_ms: float = 0.0

    # 时间戳
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "document_id": self.document_id,
            "file_path": self.file_path,
            "original_filename": self.original_filename,
            "extraction": self.extraction.to_dict(),
            "quality": {
                "score": self.quality_score,
                "completeness": self.completeness,
                "accuracy": self.accuracy,
                "consistency": self.consistency,
                "confidence": self.confidence,
            },
            "consistency_checks": {
                "errors": self.consistency_errors,
                "warnings": self.consistency_warnings,
            },
            "rule_checks": {
                "errors": self.rule_errors,
                "warnings": self.rule_warnings,
            },
            "quality_assessment": {
                "issues": self.quality_issues,
                "suggestions": self.quality_suggestions,
            },
            "status": self.status,
            "error_message": self.error_message,
            "total_processing_time_ms": self.total_processing_time_ms,
            "created_at": self.created_at,
        }

    def is_high_quality(self, threshold: float = 0.8) -> bool:
        """判断是否高质量"""
        return self.quality_score >= threshold

    def get_critical_issues(self) -> List[str]:
        """获取关键问题"""
        issues = []
        issues.extend(self.extraction.validation_errors)
        issues.extend(self.consistency_errors)
        issues.extend(self.rule_errors)
        return issues

    def has_errors(self) -> bool:
        """是否有错误"""
        return (
            len(self.extraction.validation_errors) > 0 or
            len(self.consistency_errors) > 0 or
            len(self.rule_errors) > 0
        )
