"""
API Schema定义 - 基于字段库和需求的双向校验数据模型
"""
from typing import Optional, List, Any, Dict, Literal
from pydantic import BaseModel, Field, validator, root_validator
from datetime import datetime
from decimal import Decimal

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
        """确保提供了文件路径"""
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
