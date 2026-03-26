"""
处理管道 - 端到端的文档处理流程
"""
import logging
import time
from typing import Dict, List, Any, Optional
from pathlib import Path

from .processor import DocumentProcessor
from .result import ProcessingResult, ExtractionResult

from utils.logger import get_logger
from utils.exceptions import PipelineError

logger = get_logger(__name__)


class ProcessingPipeline:
    """处理管道 - 端到端的文档处理流程"""

    def __init__(
        self,
        ocr_engine,
        llm_client,
        pdf_parser=None,
        enhance_images=True,
        clean_text=True,
    ):
        """
        初始化处理管道

        Args:
            ocr_engine: OCR引擎
            llm_client: LLM客户端
            pdf_parser: PDF解析器(可选)
            enhance_images: 是否增强图像
            clean_text: 是否清洗文本
        """
        self.processor = DocumentProcessor(
            ocr_engine=ocr_engine,
            llm_client=llm_client,
            pdf_parser=pdf_parser,
            enhance_images=enhance_images,
            clean_text=clean_text,
        )
        logger.info("处理管道初始化完成")

    def run(
        self,
        file_path: str,
        document_id: Optional[str] = None,
        target_fields: Optional[List[str]] = None,
    ) -> ProcessingResult:
        """
        运行处理管道

        Args:
            file_path: 文件路径
            document_id: 文档ID(可选)
            target_fields: 目标字段列表(可选)

        Returns:
            处理结果

        Raises:
            PipelineError: 管道执行失败时抛出
        """
        start_time = time.time()

        try:
            logger.info(f"开始处理管道: {file_path}")

            # 处理文件
            result_data = self.processor.process_file(
                file_path=file_path,
                document_id=document_id,
                target_fields=target_fields,
            )

            # 构建处理结果
            processing_result = self._build_result(result_data, start_time)

            logger.info(
                f"处理管道完成: {file_path}, "
                f"质量评分: {processing_result.quality_score:.2f}"
            )

            return processing_result

        except Exception as e:
            logger.error(f"处理管道失败: {file_path}, {e}", exc_info=True)

            # 返回失败结果
            return ProcessingResult(
                document_id=document_id or "unknown",
                file_path=file_path,
                original_filename=Path(file_path).name,
                extraction=ExtractionResult(
                    document_id=document_id or "unknown",
                    document_type="unknown",
                    document_name="未知",
                    extracted_data={},
                    extraction_time="",
                    processing_time_ms=0,
                ),
                quality_score=0.0,
                completeness=0.0,
                accuracy=0.0,
                consistency=0.0,
                confidence=0.0,
                status="failed",
                error_message=str(e),
                total_processing_time_ms=(time.time() - start_time) * 1000,
            )

    def run_batch(
        self,
        file_paths: List[str],
        target_fields: Optional[List[str]] = None,
    ) -> List[ProcessingResult]:
        """
        批量运行处理管道

        Args:
            file_paths: 文件路径列表
            target_fields: 目标字段列表

        Returns:
            处理结果列表
        """
        results = []

        for idx, file_path in enumerate(file_paths):
            logger.info(f"批量处理: {idx + 1}/{len(file_paths)}")

            result = self.run(
                file_path=file_path,
                target_fields=target_fields,
            )

            results.append(result)

        # 统计
        success_count = sum(1 for r in results if r.status == "success")
        high_quality_count = sum(1 for r in results if r.is_high_quality())

        logger.info(
            f"批量处理完成: {success_count}/{len(file_paths)} 成功, "
            f"{high_quality_count}/{len(file_paths)} 高质量"
        )

        return results

    def _build_result(
        self,
        result_data: Dict[str, Any],
        start_time: float,
    ) -> ProcessingResult:
        """构建处理结果"""
        # 提取错误和警告
        validation_errors = []
        validation_warnings = []

        for field_name, detail in result_data.get("validation_details", {}).items():
            validation_errors.extend(detail.get("errors", []))
            validation_warnings.extend(detail.get("warnings", []))

        # 规则检查错误和警告
        rule_errors = []
        rule_warnings = []

        for rule_result in self.processor.rule_checker.check(
            data=result_data["extracted_data"],
            document_type=result_data["document_type"],
        ):
            if not rule_result.is_passed:
                if rule_result.severity == "error":
                    rule_errors.append(
                        f"{rule_result.rule_name}: {rule_result.message}"
                    )
                else:
                    rule_warnings.append(
                        f"{rule_result.rule_name}: {rule_result.message}"
                    )

        # 一致性检查
        consistency_errors = []
        consistency_warnings = []

        for check_result in self.processor.consistency_checker.check(
            data=result_data["extracted_data"]
        ):
            if not check_result.is_consistent:
                if check_result.severity == "error":
                    consistency_errors.append(
                        f"{check_result.check_name}: {check_result.message}"
                    )
                else:
                    consistency_warnings.append(
                        f"{check_result.check_name}: {check_result.message}"
                    )

        # 质量评估
        quality = result_data.get("quality", {})

        # 构建提取结果
        extraction_result = ExtractionResult(
            document_id=result_data["document_id"],
            document_type=result_data["document_type"],
            document_name=result_data["document_name"],
            extracted_data=result_data["extracted_data"],
            extraction_time=result_data.get("created_at", ""),
            processing_time_ms=result_data.get("processing_time_ms", 0),
            classification_confidence=result_data.get("classification_confidence", 0),
            avg_field_confidence=result_data.get("validation", {}).get("avg_confidence", 0),
            validation_errors=validation_errors,
            validation_warnings=validation_warnings,
            raw_text=result_data.get("raw_text"),
            ocr_results=result_data.get("ocr_results"),
        )

        # 确定状态
        has_errors = (
            len(validation_errors) > 0 or
            len(rule_errors) > 0 or
            len(consistency_errors) > 0
        )

        status = "success" if not has_errors else "partial"

        # 构建完整结果
        processing_result = ProcessingResult(
            document_id=result_data["document_id"],
            file_path=result_data.get("metadata", {}).get("source_file", ""),
            original_filename=Path(
                result_data.get("metadata", {}).get("source_file", "")
            ).name,
            extraction=extraction_result,
            quality_score=quality.get("score", 0),
            completeness=quality.get("completeness", 0),
            accuracy=quality.get("accuracy", 0),
            consistency=quality.get("consistency", 0),
            confidence=quality.get("confidence", 0),
            consistency_errors=consistency_errors,
            consistency_warnings=consistency_warnings,
            rule_errors=rule_errors,
            rule_warnings=rule_warnings,
            quality_issues=quality.get("issues", []),
            quality_suggestions=quality.get("suggestions", []),
            status=status,
            total_processing_time_ms=(time.time() - start_time) * 1000,
        )

        return processing_result

    def get_pipeline_summary(
        self,
        results: List[ProcessingResult],
    ) -> Dict[str, Any]:
        """
        获取管道处理摘要

        Args:
            results: 处理结果列表

        Returns:
            摘要信息
        """
        total = len(results)
        if total == 0:
            return {"total_documents": 0}

        success = sum(1 for r in results if r.status == "success")
        partial = sum(1 for r in results if r.status == "partial")
        failed = sum(1 for r in results if r.status == "failed")

        high_quality = sum(1 for r in results if r.is_high_quality())
        with_errors = sum(1 for r in results if r.has_errors())

        avg_quality = sum(r.quality_score for r in results) / total
        avg_time = sum(r.total_processing_time_ms for r in results) / total

        # 文档类型分布
        type_distribution = {}
        for result in results:
            doc_type = result.extraction.document_type
            type_distribution[doc_type] = type_distribution.get(doc_type, 0) + 1

        return {
            "total_documents": total,
            "success": success,
            "partial": partial,
            "failed": failed,
            "high_quality": high_quality,
            "with_errors": with_errors,
            "success_rate": round(success / total * 100, 2),
            "avg_quality_score": round(avg_quality, 3),
            "avg_processing_time_ms": round(avg_time, 2),
            "type_distribution": type_distribution,
        }
