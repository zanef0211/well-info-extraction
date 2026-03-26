"""
API Schema定义 - 基于字段库和需求的双向校验数据模型
"""
from typing import Optional, List, Any, Dict, Literal
from pydantic import BaseModel, Field, validator, root_validator
from datetime import datetime

from config.field_schemas import FIELD_SCHEMAS


# ========== 请求Schema ==========

class BaseProcessRequest(BaseModel):
    """基础处理请求 - 所有处理接口的通用参数"""
    target_fields: Optional[List[str]] = Field(
        None,
        description="目标字段列表(可选),不传则提取所有字段"
    )
    category: Optional[Literal[
        "basic", "drilling", "mudlogging", "wireline",
        "testing", "completion", "geology", "production"
    ]] = Field(
        None,
        description="一级分类(可选): drilling/mudlogging/wireline/testing/completion/geology/production"
    )
    doc_category: Optional[str] = Field(
        None,
        description="二级文档分类(可选): 如'钻井设计'、'完井设计'、'钻井日报'等"
    )
    enhance_images: bool = Field(
        True,
        description="是否对图像进行增强处理"
    )
    clean_text: bool = Field(
        True,
        description="是否对文本进行清洗"
    )

    @validator('category')
    def validate_category(cls, v):
        """校验分类是否有效"""
        if v is not None and v not in FIELD_SCHEMAS.CATEGORY_MAP:
            raise ValueError(f"无效的分类: {v}, 支持的分类: {list(FIELD_SCHEMAS.CATEGORY_MAP.keys())}")
        return v

    @validator('doc_category')
    def validate_doc_category(cls, v, values):
        """校验二级分类是否与一级分类匹配"""
        if v is not None and 'category' in values and values['category']:
            category = values['category']
            doc_categories = FIELD_SCHEMAS.DOC_CATEGORIES.get(category, [])
            if v not in doc_categories:
                raise ValueError(
                    f"二级分类'{v}'不属于一级分类'{category}'。"
                    f"'{category}'支持的二级分类: {doc_categories}"
                )
        return v

    @validator('target_fields')
    def validate_target_fields(cls, v, values):
        """校验目标字段是否在字段库中"""
        if v is not None and 'category' in values and values['category']:
            category = values['category']
            valid_fields = FIELD_SCHEMAS.get_field_names(category)
            invalid_fields = [f for f in v if f not in valid_fields]
            if invalid_fields:
                raise ValueError(
                    f"无效的字段: {invalid_fields}。"
                    f"分类'{category}'支持的字段: {valid_fields[:10]}{'...' if len(valid_fields) > 10 else ''}"
                )
        return v


class ProcessRequest(BaseProcessRequest):
    """单文档处理请求 - 文件路径方式"""
    file_path: Optional[str] = Field(
        None,
        description="文件路径(可选,用于服务器本地文件)"
    )
    document_id: Optional[str] = Field(
        None,
        description="文档ID(可选)"
    )

    @root_validator
    def validate_file_path(cls, values):
        """确保至少提供文件路径或文件"""
        if not values.get('file_path'):
            raise ValueError("必须提供file_path")
        return values


class BatchProcessRequest(BaseProcessRequest):
    """批量处理请求 - 文件路径方式"""
    file_paths: List[str] = Field(
        ...,
        description="文件路径列表"
    )
    group_by_well: bool = Field(
        True,
        description="是否按井号分组(默认true)"
    )

    @validator('file_paths')
    def validate_file_paths(cls, v):
        """校验文件路径列表"""
        if not v or len(v) == 0:
            raise ValueError("文件路径列表不能为空")
        if len(v) > 100:
            raise ValueError("批量处理最多支持100个文件")
        return v


class SingleWellBatchRequest(BaseProcessRequest):
    """单井批量处理请求"""
    well_no: Optional[str] = Field(
        None,
        description="井号(可选,提供可提高准确性)"
    )
    target_categories: Optional[List[Literal[
        "basic", "drilling", "mudlogging", "wireline",
        "testing", "completion", "geology", "production"
    ]]] = Field(
        None,
        description="目标分类列表(可选)"
    )

    @validator('target_categories')
    def validate_target_categories(cls, v):
        """校验目标分类"""
        if v is not None:
            for cat in v:
                if cat not in FIELD_SCHEMAS.CATEGORY_MAP:
                    raise ValueError(f"无效的分类: {cat}")
        return v


class ValidateRequest(BaseModel):
    """验证请求"""
    data: Dict[str, Any] = Field(
        ...,
        description="待验证的数据"
    )
    document_type: Optional[str] = Field(
        None,
        description="文档类型(可选)"
    )


class QualityCheckRequest(BaseModel):
    """质量检查请求"""
    document_id: str = Field(
        ...,
        description="文档ID"
    )
    extracted_data: Dict[str, Any] = Field(
        ...,
        description="提取的数据"
    )
    target_fields: List[str] = Field(
        ...,
        description="目标字段列表"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="元数据(可选)"
    )


# ========== 响应Schema ==========

class BaseResponse(BaseModel):
    """基础响应 - 所有接口的通用响应格式"""
    success: bool = Field(
        ...,
        description="是否成功"
    )
    message: str = Field(
        ...,
        description="响应消息"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="时间戳(ISO 8601格式)"
    )
    request_id: Optional[str] = Field(
        None,
        description="请求唯一标识符(可选)"
    )


class FieldExtractionResult(BaseModel):
    """字段提取结果 - 统一的字段级别数据结构"""
    value: Any = Field(
        ...,
        description="提取的值,可以是字符串、数字、日期、null等"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="置信度(0-1),表示AI对该字段提取结果的信心"
    )
    source: Optional[str] = Field(
        None,
        description="值来源描述,如'文档第3页表格'、'文档标题'等"
    )
    unit: Optional[str] = Field(
        None,
        description="单位(如适用),如'米'、'天'、'吨/日'等"
    )
    validated: bool = Field(
        ...,
        description="是否通过规则校验"
    )

    @validator('confidence')
    def validate_confidence_range(cls, v):
        """校验置信度范围"""
        if not 0.0 <= v <= 1.0:
            raise ValueError("置信度必须在0-1之间")
        return v


class DocumentInfo(BaseModel):
    """文档信息"""
    document_id: str = Field(
        ...,
        description="文档唯一标识"
    )
    filename: str = Field(
        ...,
        description="文件名"
    )
    file_size: int = Field(
        ...,
        description="文件大小(字节)"
    )
    document_type: str = Field(
        ...,
        description="文档MIME类型"
    )
    category: Optional[str] = Field(
        None,
        description="一级分类代码"
    )
    category_name: Optional[str] = Field(
        None,
        description="一级分类名称"
    )
    doc_category: Optional[str] = Field(
        None,
        description="二级文档分类"
    )
    classification_confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="分类置信度"
    )


class WellInfo(BaseModel):
    """井信息"""
    well_no: Optional[str] = Field(
        None,
        description="井号"
    )
    well_no_confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="井号识别置信度"
    )
    is_multi_well: bool = Field(
        False,
        description="是否包含多口井"
    )


class QualityMetrics(BaseModel):
    """质量指标"""
    completeness: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="完整性(0-1)"
    )
    accuracy: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="准确性(0-1)"
    )
    consistency: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="一致性(0-1)"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="置信度(0-1)"
    )
    overall_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="总体评分(0-1)"
    )


class ValidationIssue(BaseModel):
    """校验问题"""
    field: Optional[str] = Field(
        None,
        description="字段名(可选)"
    )
    level: Literal["error", "warning", "info"] = Field(
        ...,
        description="问题级别: error/warning/info"
    )
    message: str = Field(
        ...,
        description="问题描述"
    )


class ValidationResults(BaseModel):
    """校验结果"""
    total_fields: int = Field(
        ...,
        description="总字段数"
    )
    valid_fields: int = Field(
        ...,
        description="有效字段数"
    )
    invalid_fields: int = Field(
        ...,
        description="无效字段数"
    )
    warnings: List[ValidationIssue] = Field(
        default_factory=list,
        description="警告列表"
    )
    errors: List[ValidationIssue] = Field(
        default_factory=list,
        description="错误列表"
    )

    @validator('total_fields')
    def validate_totals(cls, v, values):
        """校验字段数统计"""
        if 'valid_fields' in values and 'invalid_fields' in values:
            if v != values['valid_fields'] + values['invalid_fields']:
                raise ValueError("字段数统计不一致")
        return v


class ProcessingInfo(BaseModel):
    """处理信息"""
    processing_time_ms: int = Field(
        ...,
        ge=0,
        description="总处理时间(毫秒)"
    )
    stages: Optional[Dict[str, int]] = Field(
        None,
        description="各阶段耗时(毫秒)"
    )


class ProcessingResponse(BaseResponse):
    """单文档处理响应"""
    document_info: Optional[DocumentInfo] = Field(
        None,
        description="文档信息"
    )
    well_info: Optional[WellInfo] = Field(
        None,
        description="井信息"
    )
    extracted_fields: Dict[str, FieldExtractionResult] = Field(
        ...,
        description="提取的字段字典,键为字段名,值为字段提取结果"
    )
    validation_results: Optional[ValidationResults] = Field(
        None,
        description="校验结果"
    )
    quality_metrics: Optional[QualityMetrics] = Field(
        None,
        description="质量指标"
    )
    processing_info: Optional[ProcessingInfo] = Field(
        None,
        description="处理信息"
    )

    @validator('extracted_fields')
    def validate_extracted_fields(cls, v, values):
        """校验提取的字段是否符合字段库定义"""
        if 'document_info' in values and values['document_info'] and values['document_info'].category:
            category = values['document_info'].category
            valid_fields = FIELD_SCHEMAS.get_field_names(category)
            invalid_fields = [f for f in v.keys() if f not in valid_fields]
            if invalid_fields:
                raise ValueError(
                    f"提取了无效字段: {invalid_fields}。"
                    f"分类'{category}'支持的字段: {valid_fields}"
                )
        return v


class DocumentResult(BaseModel):
    """文档处理结果 - 批量处理中的单个文档结果"""
    document_id: str = Field(
        ...,
        description="文档ID"
    )
    filename: str = Field(
        ...,
        description="文件名"
    )
    status: Literal["success", "partial", "failed"] = Field(
        ...,
        description="处理状态"
    )
    well_no: Optional[str] = Field(
        None,
        description="井号"
    )
    category: Optional[str] = Field(
        None,
        description="一级分类"
    )
    doc_category: Optional[str] = Field(
        None,
        description="二级文档分类"
    )
    extracted_fields: Optional[Dict[str, FieldExtractionResult]] = Field(
        None,
        description="提取的字段"
    )
    quality_metrics: Optional[QualityMetrics] = Field(
        None,
        description="质量指标"
    )
    processing_time_ms: Optional[int] = Field(
        None,
        description="处理时间(毫秒)"
    )
    error_message: Optional[str] = Field(
        None,
        description="错误信息(如果失败)"
    )


class BatchInfo(BaseModel):
    """批次信息"""
    total_documents: int = Field(
        ...,
        description="总文档数"
    )
    successful_documents: int = Field(
        ...,
        description="成功处理文档数"
    )
    partial_documents: int = Field(
        ...,
        description="部分成功文档数"
    )
    failed_documents: int = Field(
        ...,
        description="失败文档数"
    )
    total_wells: int = Field(
        ...,
        description="识别到的井数"
    )
    unrecognized_wells: int = Field(
        ...,
        description="未识别到井的文档数"
    )
    processing_time_ms: int = Field(
        ...,
        description="总处理时间(毫秒)"
    )

    @root_validator
    def validate_totals(cls, values):
        """校验总数统计"""
        total_docs = values.get('total_documents', 0)
        success = values.get('successful_documents', 0)
        partial = values.get('partial_documents', 0)
        failed = values.get('failed_documents', 0)
        if total_docs != success + partial + failed:
            raise ValueError("文档数统计不一致")
        return values


class WellGroupSummary(BaseModel):
    """井分组汇总"""
    well_no: str = Field(
        ...,
        description="井号"
    )
    document_count: int = Field(
        ...,
        description="文档数量"
    )
    categories: List[str] = Field(
        ...,
        description="涉及的分类列表"
    )
    avg_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="平均置信度"
    )


class WellGroup(BaseModel):
    """井分组"""
    well_info: WellGroupSummary = Field(
        ...,
        description="井汇总信息"
    )
    documents: List[DocumentResult] = Field(
        ...,
        description="该井的文档列表"
    )


class SummaryByCategory(BaseModel):
    """按分类汇总"""
    count: int = Field(
        ...,
        description="文档数量"
    )
    avg_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="平均置信度"
    )
    avg_quality: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="平均质量"
    )


class SummaryByWell(BaseModel):
    """按井汇总"""
    well_no: str = Field(
        ...,
        description="井号"
    )
    document_count: int = Field(
        ...,
        description="文档数量"
    )
    categories: List[str] = Field(
        ...,
        description="涉及的分类列表"
    )
    avg_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="平均置信度"
    )
    avg_quality: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="平均质量"
    )


class OverallSummary(BaseModel):
    """总体汇总"""
    avg_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="平均置信度"
    )
    avg_quality: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="平均质量"
    )
    processing_speed: str = Field(
        ...,
        description="处理速度(如: '13.3 docs/minute')"
    )


class BatchProcessingSummary(BaseModel):
    """批量处理汇总"""
    by_category: Dict[str, SummaryByCategory] = Field(
        ...,
        description="按分类统计"
    )
    by_well: List[SummaryByWell] = Field(
        ...,
        description="按井统计"
    )
    overall: OverallSummary = Field(
        ...,
        description="总体统计"
    )


class BatchProcessingResponse(BaseResponse):
    """批量处理响应"""
    batch_info: BatchInfo = Field(
        ...,
        description="批次信息"
    )
    document_results: List[DocumentResult] = Field(
        ...,
        description="文档结果列表"
    )
    well_groups: Optional[Dict[str, WellGroup]] = Field(
        None,
        description="按井号分组的文档"
    )
    summary: Optional[BatchProcessingSummary] = Field(
        None,
        description="汇总统计"
    )


class FieldSource(BaseModel):
    """字段来源 - 用于字段合并"""
    document_id: str = Field(
        ...,
        description="文档ID"
    )
    value: Any = Field(
        ...,
        description="值"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="置信度"
    )


class MergedFieldResult(BaseModel):
    """合并字段结果"""
    value: Any = Field(
        ...,
        description="合并后的值"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="合并后的置信度"
    )
    sources: List[FieldSource] = Field(
        ...,
        description="来源列表"
    )
    unit: Optional[str] = Field(
        None,
        description="单位"
    )
    validated: bool = Field(
        ...,
        description="是否通过校验"
    )


class MergedFieldsByCategory(BaseModel):
    """按分类组织的合并字段"""
    category: str = Field(
        ...,
        description="分类名称"
    )
    fields: Dict[str, MergedFieldResult] = Field(
        ...,
        description="合并后的字段"
    )


class QualityByCategory(BaseModel):
    """按分类质量统计"""
    completeness: float = Field(
        ...,
        ge=0.0,
        le=1.0
    )
    accuracy: float = Field(
        ...,
        ge=0.0,
        le=1.0
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0
    )


class QualityIssue(BaseModel):
    """质量问题"""
    category: Optional[str] = Field(
        None,
        description="分类"
    )
    field: Optional[str] = Field(
        None,
        description="字段名"
    )
    issue: str = Field(
        ...,
        description="问题描述"
    )
    severity: Literal["error", "warning"] = Field(
        ...,
        description="严重程度"
    )


class QualitySummary(BaseModel):
    """质量汇总"""
    overall_quality: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="总体质量"
    )
    by_category: Dict[str, QualityByCategory] = Field(
        ...,
        description="各分类质量"
    )
    issues: List[QualityIssue] = Field(
        ...,
        description="问题列表"
    )


class ValidationSummaryExtended(BaseModel):
    """扩展的校验汇总"""
    total_fields: int = Field(
        ...,
        description="总字段数"
    )
    valid_fields: int = Field(
        ...,
        description="有效字段数"
    )
    invalid_fields: int = Field(
        ...,
        description="无效字段数"
    )
    missing_fields: int = Field(
        ...,
        description="缺失字段数"
    )
    warnings: int = Field(
        ...,
        description="警告数"
    )
    errors: int = Field(
        ...,
        description="错误数"
    )
    validation_rate: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="验证率(%)"
    )


class ExportData(BaseModel):
    """导出数据"""
    json_url: Optional[str] = Field(
        None,
        description="JSON导出URL"
    )
    excel_url: Optional[str] = Field(
        None,
        description="Excel导出URL"
    )
    database_ready: bool = Field(
        ...,
        description="是否可以入库"
    )


class SingleWellBatchResponse(BaseResponse):
    """单井批量处理响应"""
    well_info: WellInfo = Field(
        ...,
        description="井信息"
    )
    document_results: List[DocumentResult] = Field(
        ...,
        description="文档结果列表"
    )
    merged_fields: Dict[str, MergedFieldsByCategory] = Field(
        ...,
        description="按分类组织的合并字段"
    )
    quality_summary: QualitySummary = Field(
        ...,
        description="质量汇总"
    )
    validation_summary: ValidationSummaryExtended = Field(
        ...,
        description="校验汇总"
    )
    export_data: ExportData = Field(
        ...,
        description="导出数据"
    )
    processing_info: ProcessingInfo = Field(
        ...,
        description="处理信息"
    )


class ValidationResponse(BaseModel):
    """字段验证响应"""
    field_name: str = Field(
        ...,
        description="字段名"
    )
    is_valid: bool = Field(
        ...,
        description="是否有效"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="错误列表"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="警告列表"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="置信度"
    )


class ValidationSummaryResponse(BaseModel):
    """验证摘要响应"""
    total_fields: int = Field(
        ...,
        description="总字段数"
    )
    valid_fields: int = Field(
        ...,
        description="有效字段数"
    )
    invalid_fields: int = Field(
        ...,
        description="无效字段数"
    )
    total_errors: int = Field(
        ...,
        description="总错误数"
    )
    total_warnings: int = Field(
        ...,
        description="总警告数"
    )
    validation_rate: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="验证率(%)"
    )
    avg_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="平均置信度"
    )
    problem_fields: List[str] = Field(
        default_factory=list,
        description="问题字段列表"
    )


class QualityReportResponse(BaseModel):
    """质量报告响应"""
    document_id: str = Field(
        ...,
        description="文档ID"
    )
    metrics: QualityMetrics = Field(
        ...,
        description="质量指标"
    )
    issues: List[str] = Field(
        default_factory=list,
        description="问题列表"
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="建议列表"
    )
    validated_at: str = Field(
        ...,
        description="验证时间"
    )


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(
        ...,
        description="服务状态"
    )
    version: str = Field(
        ...,
        description="版本号"
    )
    models_loaded: Dict[str, bool] = Field(
        ...,
        description="模型加载状态"
    )
    storage_available: bool = Field(
        ...,
        description="存储是否可用"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="检查时间"
    )


# ========== 文档分类相关Schema ==========

class ClassificationRequest(BaseModel):
    """文档分类请求"""
    file_path: str = Field(
        ...,
        description="文件路径"
    )
    document_text: Optional[str] = Field(
        None,
        description="文档文本内容(可选,如果已提取)"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="文档元数据(可选)"
    )


class ClassificationResponse(BaseModel):
    """文档分类响应"""
    success: bool = Field(
        ...,
        description="是否成功"
    )
    category: str = Field(
        ...,
        description="一级分类代码: drilling/mudlogging/wireline/testing/completion/geology/production"
    )
    category_name: str = Field(
        ...,
        description="一级分类名称: 钻井资料/录井资料等"
    )
    doc_category: str = Field(
        ...,
        description="二级文档分类: 钻井设计/完井设计/钻井日报等"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="分类置信度(0-1)"
    )
    reason: str = Field(
        ...,
        description="分类依据"
    )
    suggested_fields: List[str] = Field(
        default_factory=list,
        description="建议提取的字段列表"
    )

    @validator('category')
    def validate_category(cls, v):
        """校验分类有效性"""
        if v not in FIELD_SCHEMAS.CATEGORY_MAP:
            raise ValueError(f"无效的分类: {v}")
        return v


class GetDocCategoriesResponse(BaseModel):
    """获取文档分类响应"""
    success: bool = Field(
        ...,
        description="是否成功"
    )
    categories: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="分类字典"
    )
