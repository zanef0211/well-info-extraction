"""
API Schema定义
"""
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime


# ========== 请求Schema ==========

class ProcessRequest(BaseModel):
    """处理请求"""
    file_path: Optional[str] = Field(None, description="文件路径(可选,用于服务器本地文件)")
    target_fields: Optional[List[str]] = Field(None, description="目标字段列表(可选)")
    document_id: Optional[str] = Field(None, description="文档ID(可选)")
    category: Optional[str] = Field(None, description="一级分类(可选): drilling/mudlogging/wireline/testing/completion/geology/production")
    doc_category: Optional[str] = Field(None, description="二级文档分类(可选): 钻井设计/完井设计/钻井日报等")
    enhance_images: bool = Field(True, description="是否增强图像")
    clean_text: bool = Field(True, description="是否清洗文本")


class BatchProcessRequest(BaseModel):
    """批量处理请求"""
    file_paths: List[str] = Field(..., description="文件路径列表")
    target_fields: Optional[List[str]] = Field(None, description="目标字段列表(可选)")
    category: Optional[str] = Field(None, description="一级分类(可选): drilling/mudlogging/wireline/testing/completion/geology/production")
    doc_category: Optional[str] = Field(None, description="二级文档分类(可选): 钻井设计/完井设计/钻井日报等")
    enhance_images: bool = Field(True, description="是否增强图像")
    clean_text: bool = Field(True, description="是否清洗文本")


class SingleWellBatchRequest(BaseModel):
    """单井批量处理请求"""
    well_no: str = Field(..., description="井号")
    file_paths: List[str] = Field(..., description="文件路径列表")
    target_fields: Optional[List[str]] = Field(None, description="目标字段列表(可选)")
    category: Optional[str] = Field(None, description="一级分类(可选): drilling/mudlogging/wireline/testing/completion/geology/production")
    doc_category: Optional[str] = Field(None, description="二级文档分类(可选): 钻井设计/完井设计/钻井日报等")
    enhance_images: bool = Field(True, description="是否增强图像")
    clean_text: bool = Field(True, description="是否清洗文本")


class ValidateRequest(BaseModel):
    """验证请求"""
    data: Dict[str, Any] = Field(..., description="待验证的数据")
    document_type: Optional[str] = Field(None, description="文档类型(可选)")


class QualityCheckRequest(BaseModel):
    """质量检查请求"""
    document_id: str = Field(..., description="文档ID")
    extracted_data: Dict[str, Any] = Field(..., description="提取的数据")
    target_fields: List[str] = Field(..., description="目标字段列表")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据(可选)")


# ========== 响应Schema ==========

class BaseResponse(BaseModel):
    """基础响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="时间戳")


class ProcessingResponse(BaseResponse):
    """处理响应"""
    data: Optional[Dict[str, Any]] = Field(None, description="处理结果数据")
    category: Optional[str] = Field(None, description="一级分类")
    doc_category: Optional[str] = Field(None, description="二级文档分类")
    classification_confidence: Optional[float] = Field(None, description="分类置信度")


class BatchProcessingResponse(BaseResponse):
    """批量处理响应"""
    data: List[Dict[str, Any]] = Field(..., description="处理结果列表")
    summary: Dict[str, Any] = Field(..., description="处理摘要")
    classifications: Optional[List[Dict[str, Any]]] = Field(None, description="分类结果列表")


class SingleWellBatchResponse(BaseResponse):
    """单井批量处理响应"""
    well_no: str = Field(..., description="井号")
    data: List[Dict[str, Any]] = Field(..., description="处理结果列表")
    summary: Dict[str, Any] = Field(..., description="处理摘要")
    total_files: int = Field(..., description="总文件数")
    successful_files: int = Field(..., description="成功文件数")
    failed_files: int = Field(..., description="失败文件数")


class ValidationResponse(BaseModel):
    """验证响应"""
    field_name: str = Field(..., description="字段名")
    is_valid: bool = Field(..., description="是否有效")
    errors: List[str] = Field(default_factory=list, description="错误列表")
    warnings: List[str] = Field(default_factory=list, description="警告列表")
    confidence: float = Field(..., description="置信度")


class ValidationSummaryResponse(BaseModel):
    """验证摘要响应"""
    total_fields: int = Field(..., description="总字段数")
    valid_fields: int = Field(..., description="有效字段数")
    invalid_fields: int = Field(..., description="无效字段数")
    total_errors: int = Field(..., description="总错误数")
    total_warnings: int = Field(..., description="总警告数")
    validation_rate: float = Field(..., description="验证率")
    avg_confidence: float = Field(..., description="平均置信度")
    problem_fields: List[str] = Field(default_factory=list, description="问题字段列表")


class QualityMetricsResponse(BaseModel):
    """质量指标响应"""
    completeness: float = Field(..., description="完整性(0-1)")
    accuracy: float = Field(..., description="准确性(0-1)")
    consistency: float = Field(..., description="一致性(0-1)")
    confidence: float = Field(..., description="置信度(0-1)")
    overall_score: float = Field(..., description="总体评分(0-1)")


class QualityReportResponse(BaseModel):
    """质量报告响应"""
    document_id: str = Field(..., description="文档ID")
    metrics: QualityMetricsResponse = Field(..., description="质量指标")
    issues: List[str] = Field(default_factory=list, description="问题列表")
    suggestions: List[str] = Field(default_factory=list, description="建议列表")
    validated_at: str = Field(..., description="验证时间")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态")
    version: str = Field(..., description="版本号")
    models_loaded: Dict[str, bool] = Field(..., description="模型加载状态")
    storage_available: bool = Field(..., description="存储是否可用")


# ========== 文档分类相关Schema ==========

class ClassifyRequest(BaseModel):
    """文档分类请求"""
    file_path: str = Field(..., description="文件路径")
    document_text: Optional[str] = Field(None, description="文档文本内容(可选,如果已提取)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="文档元数据(可选)")


class ClassificationResponse(BaseModel):
    """文档分类响应"""
    success: bool = Field(..., description="是否成功")
    category: str = Field(..., description="一级分类代码: drilling/mudlogging/wireline/testing/completion/geology/production")
    category_name: str = Field(..., description="一级分类名称: 钻井资料/录井资料等")
    doc_category: str = Field(..., description="二级文档分类: 钻井设计/完井设计/钻井日报等")
    confidence: float = Field(..., description="分类置信度(0-1)")
    reason: str = Field(..., description="分类依据")
    suggested_fields: List[str] = Field(default_factory=list, description="建议提取的字段列表")


class GetDocCategoriesResponse(BaseModel):
    """获取文档分类响应"""
    success: bool = Field(..., description="是否成功")
    categories: Dict[str, Dict[str, List[str]]] = Field(..., description="一级分类和二级分类字典")
