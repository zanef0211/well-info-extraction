"""数据库模型"""
from sqlalchemy import (
    Column, String, Integer, BigInteger, Float, Boolean, DateTime, Text,
    ForeignKey, Index, UniqueConstraint, DECIMAL, Date, Numeric
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

from .database import Base


class Well(Base):
    """井信息表 - 核心表
    
    井是整个系统的核心,所有文档、数据都关联到具体的井号。
    符合"以井为核"的设计理念。
    """
    __tablename__ = "wells"

    id = Column(Integer, primary_key=True, autoincrement=True)
    well_no = Column(String(50), unique=True, nullable=False, index=True, comment="井号")
    well_name = Column(String(200), comment="井名")
    oilfield = Column(String(100), comment="油田")
    block = Column(String(100), comment="区块")
    well_type = Column(String(50), comment="井别: 探井/开发井/注水井等")
    well_pattern = Column(String(50), comment="井型: 直井/定向井/水平井")
    well_class = Column(String(50), comment="井类")
    latitude = Column(Numeric(10, 6), comment="纬度")
    longitude = Column(Numeric(10, 6), comment="经度")
    elevation = Column(Numeric(10, 2), comment="海拔")
    ground_elevation = Column(Numeric(10, 2), comment="地面海拔")
    drill_date = Column(Date, comment="开钻日期")
    completion_date = Column(Date, comment="完井日期")
    status = Column(String(20), default='active', comment="状态: active/inactive")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    documents = relationship("Document", back_populates="well", cascade="all, delete-orphan")
    extracted_data = relationship("ExtractedData", back_populates="well", cascade="all, delete-orphan")
    quality_reports = relationship("QualityReport", back_populates="well", cascade="all, delete-orphan")
    processing_logs = relationship("ProcessingLog", back_populates="well", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index('idx_wells_well_no', 'well_no'),
        Index('idx_wells_oilfield', 'oilfield'),
        Index('idx_wells_block', 'block'),
        Index('idx_wells_status', 'status'),
    )


class Document(Base):
    """文档表
    
    每份文档必须关联到具体的井号。
    井号是文档的核心属性。
    """
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    well_no = Column(String(50), nullable=False, index=True, comment="井号")
    document_id = Column(String(100), unique=True, comment="文档ID")
    filename = Column(String(255), nullable=False, comment="文件名")
    file_path = Column(String(500), comment="文件路径")
    file_size = Column(BigInteger, comment="文件大小")
    file_extension = Column(String(10), comment="文件扩展名")
    mime_type = Column(String(100), comment="MIME类型")
    document_type = Column(String(50), comment="文档类型")
    category = Column(String(50), comment="一级文档分类: drilling/mudlogging/wireline/testing/completion/geology/production")
    doc_category = Column(String(100), comment="二级文档分类: 钻井设计/完井设计/钻井日报/固井报告等")
    upload_date = Column(Date, comment="上传日期")
    uploaded_by = Column(String(100), comment="上传者")
    status = Column(String(20), default='pending', comment="状态: pending/processing/success/failed")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    well = relationship("Well", back_populates="documents")
    extracted_data = relationship("ExtractedData", back_populates="document", cascade="all, delete-orphan")
    quality_reports = relationship("QualityReport", back_populates="document", cascade="all, delete-orphan")
    validation_results = relationship("ValidationResult", back_populates="document", cascade="all, delete-orphan")
    review_records = relationship("ReviewRecord", back_populates="document", cascade="all, delete-orphan")
    processing_logs = relationship("ProcessingLog", back_populates="document", cascade="all, delete-orphan")
    
    # 外键
    __table_args__ = (
        Index('idx_well_no', 'well_no'),
        Index('idx_category', 'category'),
        Index('idx_doc_category', 'doc_category'),
        Index('idx_status', 'status'),
        Index('idx_upload_date', 'upload_date'),
        Index('idx_document_type', 'document_type'),
    )


class ExtractedData(Base):
    """提取数据表
    
    从文档中提取的结构化数据,每个字段都记录所属文档和井号。
    井号是字段的冗余字段,便于直接按井号查询所有提取的数据。
    """
    __tablename__ = "extracted_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)
    well_no = Column(String(50), nullable=False, index=True, comment="井号")
    field_name = Column(String(100), nullable=False, comment="字段名")
    field_value = Column(Text, comment="字段值")
    field_type = Column(String(20), comment="字段类型")
    confidence = Column(Numeric(5, 2), comment="置信度")
    is_valid = Column(Boolean, default=True, comment="是否有效")
    validation_errors = Column(JSONB, comment="验证错误信息")
    source = Column(String(20), comment="来源: ocr/llm/manual")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    document = relationship("Document", back_populates="extracted_data")
    well = relationship("Well", back_populates="extracted_data")
    
    # 约束
    __table_args__ = (
        UniqueConstraint('document_id', 'field_name', name='uq_document_field'),
        Index('idx_document_id', 'document_id'),
        Index('idx_well_no', 'well_no'),
        Index('idx_field_name', 'field_name'),
        Index('idx_confidence', 'confidence'),
    )


class QualityReport(Base):
    """质量评估表
    
    对每个文档的提取质量进行评估。
    每份评估都关联到具体的文档和井号。
    """
    __tablename__ = "quality_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)
    well_no = Column(String(50), nullable=False, index=True, comment="井号")
    completeness = Column(Numeric(5, 2), comment="完整性")
    accuracy = Column(Numeric(5, 2), comment="准确性")
    consistency = Column(Numeric(5, 2), comment="一致性")
    confidence = Column(Numeric(5, 2), comment="置信度")
    overall_score = Column(Numeric(5, 2), comment="总分")
    quality_level = Column(String(20), comment="质量等级")
    issues = Column(JSONB, comment="问题列表")
    suggestions = Column(JSONB, comment="建议列表")
    validated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # 关系
    document = relationship("Document", back_populates="quality_reports")
    well = relationship("Well", back_populates="quality_reports")
    
    # 约束
    __table_args__ = (
        UniqueConstraint('document_id', name='uq_document_quality'),
        Index('idx_document_id', 'document_id'),
        Index('idx_well_no', 'well_no'),
        Index('idx_overall_score', 'overall_score'),
    )


class ValidationResult(Base):
    """校验结果表
    
    对提取的字段进行验证,记录验证结果。
    """
    __tablename__ = "validation_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)
    field_name = Column(String(100), nullable=False)
    passed = Column(Boolean, nullable=False)
    error_type = Column(String(20), comment="错误类型: missing/format/range")
    error_message = Column(Text)
    suggestion = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # 关系
    document = relationship("Document", back_populates="validation_results")
    
    # 索引
    __table_args__ = (
        Index('idx_document_id', 'document_id'),
        Index('idx_passed', 'passed'),
    )


class ReviewRecord(Base):
    """审核记录表
    
    记录人工审核和修改的历史。
    """
    __tablename__ = "review_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)
    reviewer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    original_value = Column(Text)
    corrected_value = Column(Text)
    correction_type = Column(String(20), comment="类型: accept/reject/edit")
    comment = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # 关系
    document = relationship("Document", back_populates="review_records")
    reviewer = relationship("User", back_populates="review_records")
    
    # 索引
    __table_args__ = (
        Index('idx_document_id', 'document_id'),
        Index('idx_reviewer_id', 'reviewer_id'),
    )


class ProcessingLog(Base):
    """处理日志表
    
    记录文档处理过程中的详细日志。
    每条日志都可以关联到文档和井号,便于追溯。
    """
    __tablename__ = "processing_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey('documents.id', ondelete='SET NULL'))
    well_no = Column(String(50), index=True, comment="井号")
    stage = Column(String(50), comment="处理阶段")
    status = Column(String(20), comment="状态")
    duration_ms = Column(Integer, comment="处理时长(毫秒)")
    message = Column(Text, comment="消息")
    error_message = Column(Text, comment="错误信息")
    log_metadata = Column(JSONB, comment="元数据")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # 关系
    document = relationship("Document", back_populates="processing_logs")
    well = relationship("Well", back_populates="processing_logs")
    
    # 索引
    __table_args__ = (
        Index('idx_document_id', 'document_id'),
        Index('idx_well_no', 'well_no'),
        Index('idx_stage', 'stage'),
        Index('idx_created_at', 'created_at'),
    )


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True)
    email = Column(String(100), nullable=False, unique=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(String(20), nullable=False, default='user', comment="角色: admin/reviewer/user")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime)
    
    # 关系
    review_records = relationship("ReviewRecord", back_populates="reviewer")
    
    # 索引
    __table_args__ = (
        Index('idx_username', 'username'),
        Index('idx_email', 'email'),
        Index('idx_role', 'role'),
    )


class Statistics(Base):
    """统计数据表"""
    __tablename__ = "statistics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stat_date = Column(String(10), nullable=False, unique=True, comment="统计日期: YYYY-MM-DD")
    total_documents = Column(Integer, nullable=False, default=0, comment="总文档数")
    success_documents = Column(Integer, nullable=False, default=0, comment="成功文档数")
    failed_documents = Column(Integer, nullable=False, default=0, comment="失败文档数")
    avg_confidence = Column(Numeric(5, 3), comment="平均置信度")
    avg_processing_time_ms = Column(Integer, comment="平均处理时间(毫秒)")
    total_fields_extracted = Column(Integer, default=0, comment="总提取字段数")
    manual_review_rate = Column(Numeric(5, 3), comment="人工审核率")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # 索引
    __table_args__ = (
        UniqueConstraint('stat_date', name='uq_stat_date'),
        Index('idx_stat_date', 'stat_date'),
    )
