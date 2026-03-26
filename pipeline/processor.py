"""
文档处理器 - 整合所有处理步骤 (井号优先)
"""
import logging
import time
from typing import Dict, List, Any, Optional
from pathlib import Path

from preprocess.file_handler import FileHandler
from preprocess.pdf_parser import PDFParser
from preprocess.image_processor import ImageProcessor
from preprocess.text_cleaner import TextCleaner
from preprocess.docx_parser import DocxParser
from preprocess.excel_parser import ExcelParser
from preprocess.txt_parser import TxtParser
from models.ocr_engine import OCREngine
from models.llm_client import BaseLLMClient
from models.document_classifier import DocumentClassifier
from models.wellno_extractor import WellNoExtractor
from validation.field_validator import FieldValidator
from validation.rule_checker import RuleChecker
from validation.consistency_checker import ConsistencyChecker
from validation.data_quality_checker import DataQualityChecker

from utils.logger import get_logger
from utils.exceptions import ProcessingError

logger = get_logger(__name__)


class DocumentProcessor:
    """文档处理器 - 整合所有处理步骤 (井号优先)"""

    def __init__(
        self,
        ocr_engine: OCREngine,
        llm_client: BaseLLMClient,
        pdf_parser: Optional[PDFParser] = None,
        enhance_images: bool = True,
        clean_text: bool = True,
    ):
        """
        初始化处理器

        Args:
            ocr_engine: OCR引擎
            llm_client: LLM客户端
            pdf_parser: PDF解析器(可选)
            enhance_images: 是否增强图像
            clean_text: 是否清洗文本
        """
        self.ocr_engine = ocr_engine
        self.llm_client = llm_client
        self.enhance_images = enhance_images
        self.clean_text = clean_text

        # 初始化组件
        self.file_handler = FileHandler()
        self.pdf_parser = pdf_parser or PDFParser()
        self.docx_parser = DocxParser()
        self.excel_parser = ExcelParser()
        self.txt_parser = TxtParser()
        self.image_processor = ImageProcessor()
        self.text_cleaner = TextCleaner()

        # 初始化AI模型 (注意顺序: 井号识别器优先)
        self.wellno_extractor = WellNoExtractor(llm_client)  # ✅ 井号识别器
        self.classifier = DocumentClassifier(llm_client)

        # 初始化验证组件
        self.field_validator = FieldValidator()
        self.rule_checker = RuleChecker()
        self.consistency_checker = ConsistencyChecker()
        self.quality_checker = DataQualityChecker()

        logger.info("文档处理器初始化完成 (井号优先模式)")

    def process_file(
        self,
        file_path: str,
        document_id: Optional[str] = None,
        target_fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        处理单个文件

        处理流程:
        1. 文件验证
        2. 文本提取 (根据文件类型)
        3. ✅ 井号识别 (第一步)
        4. 文档分类 (基于井号和内容)
        5. 关键信息提取 (基于井号和分类)
        6. 验证和质量评估

        Args:
            file_path: 文件路径
            document_id: 文档ID(可选)
            target_fields: 目标字段列表(可选)

        Returns:
            处理结果字典,包含:
            - document_id: 文档ID
            - file_info: 文件信息
            - well_no_result: 井号识别结果 (核心)
            - classification_result: 文档分类结果
            - extracted_data: 提取的结构化数据
            - validation_result: 验证结果
            - quality_result: 质量评估结果

        Raises:
            ProcessingError: 处理失败时抛出
        """
        start_time = time.time()

        try:
            logger.info(f"开始处理文件: {file_path}")

            # ========== 第1步: 文件验证 ==========
            validation = self.file_handler.validate_file(file_path)
            file_ext = validation["file_extension"]
            filename = Path(file_path).name

            # 生成文档ID
            if document_id is None:
                document_id = f"doc_{int(time.time() * 1000)}"

            # ========== 第2步: 文本提取 ==========
            text, raw_text = self._extract_text_by_type(file_path, file_ext)
            logger.debug(f"文本提取完成: {len(text)} 字符")

            # ========== 第3步: 井号识别 (核心步骤) ==========
            logger.info(f"开始识别井号: {filename}")
            well_no_result = self.wellno_extractor.extract(
                filename=filename,
                content=text,
                use_llm=True,
                min_confidence=0.6,
            )

            # 如果未识别到井号,记录警告
            if not well_no_result.primary_well:
                logger.warning(f"未识别到井号: {filename}")

            # ========== 第4步: 文档分类 ==========
            logger.info(f"开始文档分类: {filename}")
            metadata = {
                "filename": filename,
                "well_no": well_no_result.primary_well,
                "file_type": file_ext,
            }

            classification_result = self.classifier.classify(
                document_text=text,
                metadata=metadata,
                top_k=1,
            )

            # ========== 第5步: 关键信息提取 ==========
            logger.info(f"开始提取关键信息: {filename}")
            extracted_data = self._extract_key_information(
                text=text,
                document_type=classification_result.document_type,
                document_id=document_id,
                target_fields=target_fields,
            )

            # 确保井号字段存在
            if well_no_result.primary_well and "WellNo" not in extracted_data:
                extracted_data["WellNo"] = well_no_result.primary_well

            # ========== 第6步: 验证 ==========
            logger.info(f"开始验证数据: {filename}")
            validation_result = self._validate_data(
                extracted_data=extracted_data,
                document_type=classification_result.document_type,
            )

            # ========== 第7步: 质量评估 ==========
            logger.info(f"开始质量评估: {filename}")
            quality_result = self._assess_quality(
                extracted_data=extracted_data,
                validation_result=validation_result,
                classification_result=classification_result,
            )

            # ========== 构建结果 ==========
            processing_time = (time.time() - start_time) * 1000

            result = {
                "document_id": document_id,
                "file_info": {
                    "file_path": file_path,
                    "file_name": filename,
                    "file_size": validation["file_size"],
                    "file_extension": file_ext,
                },
                "well_no_result": {
                    "primary_well": well_no_result.primary_well,
                    "all_wells": well_no_result.all_wells,
                    "confidence": well_no_result.confidence,
                    "source": well_no_result.source,
                },
                "classification_result": {
                    "document_type": classification_result.document_type,
                    "document_name": classification_result.document_name,
                    "confidence": classification_result.confidence,
                    "reason": classification_result.reason,
                    "suggested_fields": classification_result.suggested_fields,
                },
                "extracted_data": extracted_data,
                "validation_result": validation_result,
                "quality_result": quality_result,
                "processing_time_ms": processing_time,
                "status": "success",
            }

            logger.info(
                f"文件处理完成: {filename}, "
                f"井号={well_no_result.primary_well}, "
                f"分类={classification_result.document_type}, "
                f"耗时: {processing_time:.0f}ms"
            )

            return result

        except Exception as e:
            logger.error(f"文件处理失败: {file_path}, {e}", exc_info=True)
            raise ProcessingError(f"文件处理失败: {str(e)}") from e

    def _extract_text_by_type(
        self,
        file_path: str,
        file_ext: str,
    ) -> tuple:
        """
        根据文件类型提取文本

        Returns:
            (cleaned_text, raw_text)
        """
        raw_text = ""

        # 根据文件类型提取
        if file_ext == ".pdf":
            raw_text = self.pdf_parser.extract_text(file_path)
        elif file_ext in (".docx", ".doc"):
            raw_text = self.docx_parser.extract_text(file_path)
        elif file_ext in (".xlsx", ".xls"):
            raw_text = self.excel_parser.extract_text(file_path)
        elif file_ext == ".txt":
            raw_text = self.txt_parser.extract_text(file_path)
        elif file_ext in (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"):
            # 图像需要OCR
            if self.enhance_images:
                image = self.image_processor.enhance_for_ocr(file_path)
                ocr_result = self.ocr_engine.recognize(image)
            else:
                ocr_result = self.ocr_engine.recognize(file_path)

            raw_text = " ".join([line["text"] for line in ocr_result])
        else:
            raise ProcessingError(f"不支持的文件类型: {file_ext}")

        # 清洗文本
        if self.clean_text:
            cleaned_text = self.text_cleaner.clean(raw_text)
        else:
            cleaned_text = raw_text

        return cleaned_text, raw_text

    def _extract_key_information(
        self,
        text: str,
        document_type: str,
        document_id: str,
        target_fields: Optional[List[str]],
    ) -> Dict[str, Any]:
        """
        提取关键信息

        注意: 井号已在前面识别,这里只需要提取其他字段
        """
        from pipeline.extractor import DocumentExtractor

        extractor = DocumentExtractor(self.llm_client, max_retries=2)

        # 提取数据
        data = extractor.extract(
            document_text=text,
            document_type=document_type,
            document_id=document_id,
            target_fields=target_fields,
        )

        return data

    def _validate_data(
        self,
        extracted_data: Dict[str, Any],
        document_type: str,
    ) -> Dict[str, Any]:
        """验证数据"""
        # 字段验证
        field_validation = self.field_validator.validate_fields(
            data=extracted_data,
            document_type=document_type,
        )

        # 规则检查
        rule_check = self.rule_checker.check_rules(extracted_data)

        # 一致性检查
        consistency_check = self.consistency_checker.check_consistency(extracted_data)

        return {
            "field_validation": field_validation,
            "rule_check": rule_check,
            "consistency_check": consistency_check,
        }

    def _assess_quality(
        self,
        extracted_data: Dict[str, Any],
        validation_result: Dict[str, Any],
        classification_result,
    ) -> Dict[str, Any]:
        """评估数据质量"""
        quality = self.quality_checker.check_quality(
            data=extracted_data,
            validation=validation_result,
            classification_confidence=classification_result.confidence,
        )

        return quality

    def process_batch(
        self,
        file_paths: List[str],
    ) -> List[Dict[str, Any]]:
        """
        批量处理文件

        Args:
            file_paths: 文件路径列表

        Returns:
            处理结果列表
        """
        logger.info(f"开始批量处理: {len(file_paths)} 个文件")

        results = []
        for file_path in file_paths:
            try:
                result = self.process_file(file_path)
                results.append(result)
            except Exception as e:
                logger.error(f"处理失败: {file_path}, {e}")
                results.append({
                    "file_path": file_path,
                    "status": "failed",
                    "error": str(e),
                })

        logger.info(f"批量处理完成: 成功 {len([r for r in results if r.get('status') == 'success'])}/{len(file_paths)}")

        return results

    def group_by_well_no(
        self,
        results: List[Dict[str, Any]],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        按井号分组结果

        Args:
            results: 处理结果列表

        Returns:
            按井号分组的文档字典
        """
        return self.wellno_extractor.deduplicate_and_group(results)
