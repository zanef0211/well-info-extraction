"""
CRUD操作 - 数据库增删改查
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

from db.models import (
    Well, Document, ExtractedData, QualityReport,
    ValidationResult, ProcessingLog, User, ReviewRecord
)
from config.field_schemas import FIELD_SCHEMAS


class WellCRUD:
    """井信息CRUD操作"""

    @staticmethod
    def get_or_create_well(db: Session, well_no: str) -> Well:
        """
        获取或创建井记录

        Args:
            db: 数据库会话
            well_no: 井号

        Returns:
            Well对象
        """
        # 先尝试获取已存在的记录
        well = db.query(Well).filter(Well.well_no == well_no).first()

        # 如果不存在，创建新记录
        if not well:
            well = Well(
                well_no=well_no,
                status='active'
            )
            db.add(well)
            db.commit()
            db.refresh(well)

        return well

    @staticmethod
    def get_well(db: Session, well_no: str) -> Optional[Well]:
        """获取井信息"""
        return db.query(Well).filter(Well.well_no == well_no).first()

    @staticmethod
    def update_well_info(db: Session, well_no: str, data: Dict[str, Any]) -> Optional[Well]:
        """更新井信息"""
        well = WellCRUD.get_well(db, well_no)
        if well:
            for key, value in data.items():
                if hasattr(well, key):
                    setattr(well, key, value)
            well.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(well)
        return well

    @staticmethod
    def get_all_wells(db: Session, skip: int = 0, limit: int = 100) -> List[Well]:
        """获取所有井"""
        return db.query(Well).offset(skip).limit(limit).all()

    @staticmethod
    def get_wells_by_oilfield(db: Session, oilfield: str) -> List[Well]:
        """按油田获取井"""
        return db.query(Well).filter(Well.oilfield == oilfield).all()


class DocumentCRUD:
    """文档CRUD操作"""

    @staticmethod
    def create_document(
        db: Session,
        well_no: str,
        document_id: str,
        filename: str,
        file_path: str,
        file_size: int,
        category: Optional[str] = None,
        doc_category: Optional[str] = None,
    ) -> Document:
        """
        创建文档记录

        注意：此方法会先创建或更新 Well 记录，确保外键约束有效

        Args:
            db: 数据库会话
            well_no: 井号
            document_id: 文档ID (UUID字符串)
            filename: 文件名
            file_path: 文件路径
            file_size: 文件大小
            category: 分类
            doc_category: 二级分类

        Returns:
            Document对象 (包含自增的 id)
        """
        # 【关键步骤1】先创建或获取井记录，确保外键约束有效
        well = WellCRUD.get_or_create_well(db, well_no)

        # 【关键步骤2】创建文档记录
        document = Document(
            well_no=well_no,  # 关联到已存在的井记录
            document_id=document_id,  # 文档UUID (String(100))
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            file_extension=filename.split('.')[-1].lower() if '.' in filename else None,
            category=category,
            doc_category=doc_category,
            status='processing',  # 初始状态为处理中
            upload_date=datetime.utcnow().date()
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        return document

    @staticmethod
    def update_document_status_by_id(
        db: Session,
        document_db_id: int,  # ✅ 修复：使用自增的 id (Integer)
        status: str
    ) -> Optional[Document]:
        """
        更新文档状态 (使用自增的 id)

        Args:
            db: 数据库会话
            document_db_id: 文档数据库ID (自增的整数主键)
            status: 新状态

        Returns:
            Document对象
        """
        document = db.query(Document).filter(
            Document.id == document_db_id  # ✅ 修复：查询主键 id
        ).first()
        if document:
            document.status = status
            document.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(document)
        return document

    @staticmethod
    def update_document_status_by_uuid(
        db: Session,
        document_uuid: str,  # 使用 document_id (UUID字符串)
        status: str
    ) -> Optional[Document]:
        """
        更新文档状态 (使用文档UUID)

        Args:
            db: 数据库会话
            document_uuid: 文档UUID (document_id字段)
            status: 新状态

        Returns:
            Document对象
        """
        document = db.query(Document).filter(
            Document.document_id == document_uuid  # ✅ 查询 document_id 字段
        ).first()
        if document:
            document.status = status
            document.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(document)
        return document

    @staticmethod
    def get_document_by_uuid(db: Session, document_uuid: str) -> Optional[Document]:
        """
        获取文档 (使用文档UUID)

        Args:
            db: 数据库会话
            document_uuid: 文档UUID (document_id字段)

        Returns:
            Document对象
        """
        return db.query(Document).filter(
            Document.document_id == document_uuid
        ).first()

    @staticmethod
    def get_document_by_id(db: Session, document_db_id: int) -> Optional[Document]:
        """
        获取文档 (使用自增的 id)

        Args:
            db: 数据库会话
            document_db_id: 文档数据库ID (自增的整数主键)

        Returns:
            Document对象
        """
        return db.query(Document).filter(
            Document.id == document_db_id
        ).first()

    @staticmethod
    def get_documents_by_well(db: Session, well_no: str) -> List[Document]:
        """按井号获取文档"""
        return db.query(Document).filter(Document.well_no == well_no).all()


class ExtractedDataCRUD:
    """提取数据CRUD操作"""

    @staticmethod
    def batch_create_extracted_data(
        db: Session,
        extracted_data_list: List[Dict[str, Any]]
    ) -> List[ExtractedData]:
        """
        批量创建提取数据

        Args:
            db: 数据库会话
            extracted_data_list: 提取数据列表，每个元素必须包含 document_id (int)

        Returns:
            ExtractedData对象列表
        """
        records = []
        for data in extracted_data_list:
            # ✅ 确保 document_id 是整数
            doc_id = data['document_id']
            if not isinstance(doc_id, int):
                raise TypeError(f"document_id 必须是整数，但得到 {type(doc_id)}")

            record = ExtractedData(
                document_id=doc_id,  # ✅ 必须是整数
                well_no=data['well_no'],
                field_name=data['field_name'],
                field_value=data.get('field_value'),
                field_type=data.get('field_type'),
                confidence=data.get('confidence'),
                is_valid=data.get('is_valid', True),
                validation_errors=data.get('validation_errors'),
                source=data.get('source', 'llm')
            )
            records.append(record)

        db.add_all(records)
        db.commit()

        # 刷新所有记录以获取ID
        for record in records:
            db.refresh(record)

        return records

    @staticmethod
    def get_extracted_data_by_well(db: Session, well_no: str) -> List[ExtractedData]:
        """按井号获取提取数据"""
        return db.query(ExtractedData).filter(
            ExtractedData.well_no == well_no
        ).all()

    @staticmethod
    def get_extracted_data_by_document(db: Session, document_db_id: int) -> List[ExtractedData]:
        """
        按文档ID获取提取数据

        Args:
            db: 数据库会话
            document_db_id: 文档数据库ID (自增的整数主键)

        Returns:
            ExtractedData列表
        """
        return db.query(ExtractedData).filter(
            ExtractedData.document_id == document_db_id
        ).all()


class QualityReportCRUD:
    """质量报告CRUD操作"""

    @staticmethod
    def create_quality_report(
        db: Session,
        document_db_id: int,  # ✅ 修复：使用自增的 id (Integer)
        well_no: str,
        report_data: Dict[str, Any]
    ) -> QualityReport:
        """
        创建质量报告

        Args:
            db: 数据库会话
            document_db_id: 文档数据库ID (自增的整数主键) ✅ 修复
            well_no: 井号
            report_data: 报告数据

        Returns:
            QualityReport对象
        """
        # ✅ 确保 document_db_id 是整数
        if not isinstance(document_db_id, int):
            raise TypeError(f"document_db_id 必须是整数，但得到 {type(document_db_id)}")

        report = QualityReport(
            document_id=document_db_id,  # ✅ 修复：传入整数
            well_no=well_no,
            completeness=report_data.get('completeness'),
            accuracy=report_data.get('accuracy'),
            consistency=report_data.get('consistency'),
            confidence=report_data.get('confidence'),
            overall_score=report_data.get('overall_score'),
            quality_level=report_data.get('quality_level'),
            issues=report_data.get('issues'),
            suggestions=report_data.get('suggestions')
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        return report

    @staticmethod
    def get_quality_reports_by_well(db: Session, well_no: str) -> List[QualityReport]:
        """按井号获取质量报告"""
        return db.query(QualityReport).filter(
            QualityReport.well_no == well_no
        ).all()

    @staticmethod
    def get_quality_report_by_document(db: Session, document_db_id: int) -> Optional[QualityReport]:
        """
        按文档ID获取质量报告

        Args:
            db: 数据库会话
            document_db_id: 文档数据库ID (自增的整数主键)

        Returns:
            QualityReport对象
        """
        return db.query(QualityReport).filter(
            QualityReport.document_id == document_db_id
        ).first()


class ValidationResultCRUD:
    """验证结果CRUD操作"""

    @staticmethod
    def batch_create_validation_results(
        db: Session,
        validation_results_list: List[Dict[str, Any]]
    ) -> List[ValidationResult]:
        """
        批量创建验证结果

        Args:
            db: 数据库会话
            validation_results_list: 验证结果列表，每个元素必须包含 document_id (int)

        Returns:
            ValidationResult对象列表
        """
        records = []
        for data in validation_results_list:
            # ✅ 确保 document_id 是整数
            doc_id = data['document_id']
            if not isinstance(doc_id, int):
                raise TypeError(f"document_id 必须是整数，但得到 {type(doc_id)}")

            record = ValidationResult(
                document_id=doc_id,  # ✅ 修复：传入整数
                field_name=data['field_name'],
                passed=data['passed'],
                error_type=data.get('error_type'),
                error_message=data.get('error_message'),
                suggestion=data.get('suggestion')
            )
            records.append(record)

        db.add_all(records)
        db.commit()

        # 刷新所有记录以获取ID
        for record in records:
            db.refresh(record)

        return records

    @staticmethod
    def get_validation_results_by_document(db: Session, document_db_id: int) -> List[ValidationResult]:
        """
        按文档ID获取验证结果

        Args:
            db: 数据库会话
            document_db_id: 文档数据库ID (自增的整数主键)

        Returns:
            ValidationResult列表
        """
        return db.query(ValidationResult).filter(
            ValidationResult.document_id == document_db_id
        ).all()


class ProcessingLogCRUD:
    """处理日志CRUD操作"""

    @staticmethod
    def create_processing_log(
        db: Session,
        log_data: Dict[str, Any]
    ) -> ProcessingLog:
        """
        创建处理日志

        Args:
            db: 数据库会话
            log_data: 日志数据

        Returns:
            ProcessingLog对象
        """
        # ✅ 确保 document_id 是整数或 None
        doc_id = log_data.get('document_id')
        if doc_id is not None and not isinstance(doc_id, int):
            raise TypeError(f"document_id 必须是整数或 None，但得到 {type(doc_id)}")

        # ✅ 确保 log_metadata 是有效的 JSON
        log_metadata = log_data.get('log_metadata')
        if log_metadata is not None and not isinstance(log_metadata, (dict, str)):
            raise TypeError(f"log_metadata 必须是字典或 JSON 字符串，但得到 {type(log_metadata)}")

        # 如果是字符串，尝试解析为 JSON
        if isinstance(log_metadata, str):
            try:
                log_metadata = json.loads(log_metadata)
            except json.JSONDecodeError:
                raise ValueError("log_metadata 不是有效的 JSON 字符串")

        log = ProcessingLog(
            document_id=doc_id,  # ✅ 修复：确保是整数或 None
            well_no=log_data.get('well_no'),
            stage=log_data.get('stage'),
            status=log_data.get('status'),
            duration_ms=log_data.get('duration_ms'),
            message=log_data.get('message'),
            error_message=log_data.get('error_message'),
            log_metadata=log_metadata  # ✅ 确保是有效的 JSON
        )
        db.add(log)
        db.commit()
        db.refresh(log)

        return log

    @staticmethod
    def get_processing_logs_by_well(db: Session, well_no: str, limit: int = 100) -> List[ProcessingLog]:
        """按井号获取处理日志"""
        return db.query(ProcessingLog).filter(
            ProcessingLog.well_no == well_no
        ).order_by(ProcessingLog.created_at.desc()).limit(limit).all()


class ReviewRecordCRUD:
    """审核记录CRUD操作"""

    @staticmethod
    def create_review_record(
        db: Session,
        document_db_id: int,  # ✅ 修复：使用自增的 id (Integer)
        reviewer_id: int,
        original_value: str,
        corrected_value: str,
        correction_type: str,
        comment: Optional[str] = None
    ) -> ReviewRecord:
        """
        创建审核记录

        Args:
            db: 数据库会话
            document_db_id: 文档数据库ID (自增的整数主键) ✅ 修复
            reviewer_id: 审核者ID (必须是整数)
            original_value: 原始值
            corrected_value: 修正值
            correction_type: 修正类型
            comment: 评论

        Returns:
            ReviewRecord对象
        """
        # ✅ 类型检查
        if not isinstance(document_db_id, int):
            raise TypeError(f"document_db_id 必须是整数，但得到 {type(document_db_id)}")
        if not isinstance(reviewer_id, int):
            raise TypeError(f"reviewer_id 必须是整数，但得到 {type(reviewer_id)}")

        record = ReviewRecord(
            document_id=document_db_id,  # ✅ 修复：传入整数
            reviewer_id=reviewer_id,
            original_value=original_value,
            corrected_value=corrected_value,
            correction_type=correction_type,
            comment=comment
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        return record

    @staticmethod
    def get_review_records_by_document(db: Session, document_db_id: int) -> List[ReviewRecord]:
        """
        按文档ID获取审核记录

        Args:
            db: 数据库会话
            document_db_id: 文档数据库ID (自增的整数主键)

        Returns:
            ReviewRecord列表
        """
        return db.query(ReviewRecord).filter(
            ReviewRecord.document_id == document_db_id
        ).all()


class UserCRUD:
    """用户CRUD操作"""

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """
        根据用户ID获取用户

        Args:
            db: 数据库会话
            user_id: 用户ID (自增的整数主键)

        Returns:
            User对象
        """
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def create_user(
        db: Session,
        username: str,
        email: str,
        hashed_password: str,
        full_name: Optional[str] = None,
        role: str = 'user'
    ) -> User:
        """
        创建用户

        Args:
            db: 数据库会话
            username: 用户名
            email: 邮箱
            hashed_password: 密码哈希
            full_name: 全名
            role: 角色

        Returns:
            User对象
        """
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            role=role
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        return user


def save_processing_result_to_database(
    db: Session,
    well_no: str,
    document_uuid: str,  # 文档UUID (document_id字段)
    filename: str,
    file_path: str,
    file_size: int,
    category: Optional[str] = None,
    doc_category: Optional[str] = None,
    extracted_fields: Optional[Dict[str, Any]] = None,
    quality_report: Optional[Dict[str, Any]] = None,
    validation_results: Optional[List[Dict[str, Any]]] = None,
    processing_logs: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    将处理结果保存到数据库

    数据流转流程 (修复后):
    1. 创建/更新 Well 记录 (先于 Document)
    2. 创建 Document 记录 (status='processing')，获得自增的 document.id
    3. 批量插入 ExtractedData 记录 (使用 document.id)
    4. 插入 QualityReport 记录 (使用 document.id) ✅ 修复
    5. 批量插入 ValidationResult 记录 (使用 document.id) ✅ 修复
    6. 插入 ProcessingLog 记录 (使用 document.id) ✅ 修复
    7. 更新 Document 记录 (status='success')

    Args:
        db: 数据库会话
        well_no: 井号
        document_uuid: 文档UUID (document_id字段) ✅ 修复
        filename: 文件名
        file_path: 文件路径
        file_size: 文件大小
        category: 分类
        doc_category: 二级分类
        extracted_fields: 提取字段
        quality_report: 质量报告
        validation_results: 验证结果
        processing_logs: 处理日志

    Returns:
        包含所有记录ID的字典
    """
    try:
        # 开始事务
        db.begin()

        # 【关键步骤1】创建或更新 Well 记录
        well = WellCRUD.get_or_create_well(db, well_no)
        logger.info(f"步骤1: Well 记录创建/更新成功 - {well_no}")

        # 【关键步骤2】创建 Document 记录
        document = DocumentCRUD.create_document(
            db=db,
            well_no=well_no,
            document_id=document_uuid,  # ✅ 传入 UUID
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            category=category,
            doc_category=doc_category
        )
        logger.info(f"步骤2: Document 记录创建成功 - UUID: {document_uuid}, DB ID: {document.id}")

        # ✅ 关键：使用 document.id (自增整数) 作为外键
        document_db_id = document.id

        result = {
            'well_id': well.id,
            'document_db_id': document_db_id,
            'document_uuid': document_uuid,
            'extracted_data_ids': [],
            'quality_report_id': None,
            'validation_result_ids': [],
            'processing_log_ids': []
        }

        # 【关键步骤3】批量插入 ExtractedData 记录
        if extracted_fields:
            extracted_data_list = []
            for field_name, field_data in extracted_fields.items():
                extracted_data_list.append({
                    'document_id': document_db_id,  # ✅ 修复：使用整数
                    'well_no': well_no,
                    'field_name': field_name,
                    'field_value': field_data.get('value'),
                    'field_type': field_data.get('type'),
                    'confidence': field_data.get('confidence'),
                    'is_valid': field_data.get('validated', True),
                    'validation_errors': field_data.get('validation_errors'),
                    'source': field_data.get('source', 'llm')
                })

            extracted_data_records = ExtractedDataCRUD.batch_create_extracted_data(
                db=db,
                extracted_data_list=extracted_data_list
            )
            result['extracted_data_ids'] = [r.id for r in extracted_data_records]
            logger.info(f"步骤3: ExtractedData 记录批量插入成功 - {len(extracted_data_records)} 条")

        # 【关键步骤4】插入 QualityReport 记录 ✅ 修复
        if quality_report:
            quality_report_record = QualityReportCRUD.create_quality_report(
                db=db,
                document_db_id=document_db_id,  # ✅ 修复：传入整数
                well_no=well_no,
                report_data=quality_report
            )
            result['quality_report_id'] = quality_report_record.id
            logger.info(f"步骤4: QualityReport 记录插入成功 - {quality_report_record.id}")

        # 【关键步骤5】批量插入 ValidationResult 记录 ✅ 修复
        if validation_results:
            validation_results_list = []
            for validation_result in validation_results:
                validation_results_list.append({
                    'document_id': document_db_id,  # ✅ 修复：使用整数
                    'field_name': validation_result.get('field_name'),
                    'passed': validation_result.get('passed', True),
                    'error_type': validation_result.get('error_type'),
                    'error_message': validation_result.get('error_message'),
                    'suggestion': validation_result.get('suggestion')
                })

            validation_result_records = ValidationResultCRUD.batch_create_validation_results(
                db=db,
                validation_results_list=validation_results_list
            )
            result['validation_result_ids'] = [r.id for r in validation_result_records]
            logger.info(f"步骤5: ValidationResult 记录批量插入成功 - {len(validation_result_records)} 条")

        # 【关键步骤6】插入 ProcessingLog 记录 ✅ 修复
        if processing_logs:
            processing_log_ids = []
            for log_data in processing_logs:
                log_data['well_no'] = well_no
                log_data['document_id'] = document_db_id  # ✅ 修复：使用整数
                log = ProcessingLogCRUD.create_processing_log(db=db, log_data=log_data)
                processing_log_ids.append(log.id)
            result['processing_log_ids'] = processing_log_ids
            logger.info(f"步骤6: ProcessingLog 记录插入成功 - {len(processing_logs)} 条")

        # 【关键步骤7】更新 Document 状态为 'success' ✅ 修复
        document = DocumentCRUD.update_document_status_by_id(
            db=db,
            document_db_id=document_db_id,  # ✅ 修复：使用自增的 id
            status='success'
        )
        logger.info(f"步骤7: Document 状态更新为 success - DB ID: {document_db_id}, UUID: {document_uuid}")

        # 提交事务
        db.commit()
        logger.info(f"所有数据持久化成功 - 文档UUID: {document_uuid}, 井号: {well_no}")

        return result

    except Exception as e:
        # 回滚事务
        db.rollback()
        logger.error(f"数据持久化失败: {e}", exc_info=True)
        raise
