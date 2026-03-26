"""
数据质量检查器 - 评估提取数据的质量
"""
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from utils.logger import get_logger
from validation.field_validator import FieldValidator

logger = get_logger(__name__)


@dataclass
class QualityMetrics:
    """质量指标"""
    completeness: float  # 完整性(0-1)
    accuracy: float  # 准确性(0-1)
    consistency: float  # 一致性(0-1)
    confidence: float  # 置信度(0-1)
    overall_score: float  # 总体评分(0-1)


@dataclass
class QualityReport:
    """质量报告"""
    document_id: str
    metrics: QualityMetrics
    issues: List[str]
    suggestions: List[str]
    validated_at: str


class DataQualityChecker:
    """数据质量检查器"""

    def __init__(self):
        """初始化数据质量检查器"""
        self.field_validator = FieldValidator()
        logger.info("数据质量检查器初始化完成")

    def check_quality(
        self,
        document_id: str,
        extracted_data: Dict[str, Any],
        target_fields: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> QualityReport:
        """
        检查数据质量

        Args:
            document_id: 文档ID
            extracted_data: 提取的数据
            target_fields: 目标字段列表
            metadata: 元数据

        Returns:
            质量报告
        """
        logger.info(f"开始检查数据质量: {document_id}")

        # 1. 评估完整性
        completeness = self._check_completeness(extracted_data, target_fields)

        # 2. 评估准确性(通过字段验证)
        accuracy = self._check_accuracy(extracted_data)

        # 3. 评估一致性
        consistency = self._check_consistency(extracted_data)

        # 4. 计算置信度
        confidence = self._calculate_confidence(extracted_data)

        # 5. 计算总体评分
        overall_score = (
            completeness * 0.3 +
            accuracy * 0.4 +
            consistency * 0.2 +
            confidence * 0.1
        )

        # 6. 生成问题和建议
        issues, suggestions = self._generate_issues_and_suggestions(
            extracted_data,
            completeness,
            accuracy,
            consistency,
            confidence,
        )

        metrics = QualityMetrics(
            completeness=completeness,
            accuracy=accuracy,
            consistency=consistency,
            confidence=confidence,
            overall_score=overall_score,
        )

        report = QualityReport(
            document_id=document_id,
            metrics=metrics,
            issues=issues,
            suggestions=suggestions,
            validated_at=datetime.now().isoformat(),
        )

        logger.info(
            f"质量检查完成: 总体评分={overall_score:.2f}, "
            f"完整性={completeness:.2f}, 准确性={accuracy:.2f}"
        )

        return report

    def _check_completeness(
        self,
        data: Dict[str, Any],
        target_fields: List[str],
    ) -> float:
        """
        检查完整性

        Args:
            data: 提取的数据
            target_fields: 目标字段列表

        Returns:
            完整性分数(0-1)
        """
        if not target_fields:
            return 1.0

        filled_count = 0
        for field in target_fields:
            if field in data and data[field] is not None and data[field] != "":
                filled_count += 1

        completeness = filled_count / len(target_fields)
        logger.debug(f"完整性: {filled_count}/{len(target_fields)} = {completeness:.2f}")

        return completeness

    def _check_accuracy(self, data: Dict[str, Any]) -> float:
        """
        检查准确性(基于字段验证结果)

        Args:
            data: 提取的数据

        Returns:
            准确性分数(0-1)
        """
        if not data:
            return 0.0

        validation_results = self.field_validator.validate_batch(data)
        summary = self.field_validator.get_validation_summary(validation_results)

        # 准确性 = 通过验证的字段比例
        accuracy = summary["validation_rate"] / 100
        logger.debug(f"准确性: {accuracy:.2f}")

        return accuracy

    def _check_consistency(self, data: Dict[str, Any]) -> float:
        """
        检查一致性

        Args:
            data: 提取的数据

        Returns:
            一致性分数(0-1)
        """
        # 简化检查: 检查数值关系是否合理
        checks = 0
        passed = 0

        # 井深关系: 斜深 >= 垂深
        if "斜深" in data and "垂深" in data:
            checks += 1
            try:
                oblique = float(data["斜深"])
                vertical = float(data["垂深"])
                if oblique >= vertical:
                    passed += 1
            except (ValueError, TypeError):
                pass

        # 日期关系: 开钻 <= 完钻
        if "开钻日期" in data and "完钻日期" in data:
            checks += 1
            start_date = self._parse_date(data["开钻日期"])
            end_date = self._parse_date(data["完钻日期"])
            if start_date and end_date and start_date <= end_date:
                passed += 1

        if checks == 0:
            return 1.0  # 无数据可检查,返回满分

        consistency = passed / checks
        logger.debug(f"一致性: {passed}/{checks} = {consistency:.2f}")

        return consistency

    def _calculate_confidence(self, data: Dict[str, Any]) -> float:
        """
        计算置信度

        Args:
            data: 提取的数据

        Returns:
            置信度(0-1)
        """
        if not data:
            return 0.0

        # 基于字段验证的置信度
        validation_results = self.field_validator.validate_batch(data)
        confidences = [r.confidence for r in validation_results.values()]

        if not confidences:
            return 0.0

        avg_confidence = sum(confidences) / len(confidences)
        logger.debug(f"平均置信度: {avg_confidence:.2f}")

        return avg_confidence

    def _generate_issues_and_suggestions(
        self,
        data: Dict[str, Any],
        completeness: float,
        accuracy: float,
        consistency: float,
        confidence: float,
    ) -> tuple[List[str], List[str]]:
        """
        生成问题和建议

        Args:
            data: 提取的数据
            completeness: 完整性分数
            accuracy: 准确性分数
            consistency: 一致性分数
            confidence: 置信度

        Returns:
            (问题列表, 建议列表)
        """
        issues = []
        suggestions = []

        # 完整性问题
        if completeness < 0.8:
            issues.append(f"数据完整性较低({completeness:.1%}),部分字段未提取")
            suggestions.append("建议人工复核文档,补充缺失字段")

        # 准确性问题
        if accuracy < 0.8:
            issues.append(f"部分字段格式不符合要求(准确性:{accuracy:.1%})")
            suggestions.append("建议人工验证提取的字段值")

        # 一致性问题
        if consistency < 0.8:
            issues.append(f"数据间存在逻辑不一致(一致性:{consistency:.1%})")
            suggestions.append("建议检查相关字段间的逻辑关系")

        # 置信度问题
        if confidence < 0.7:
            issues.append(f"提取置信度较低({confidence:.1%}),可能需要人工确认")
            suggestions.append("建议对低置信度字段进行人工校验")

        # 具体字段问题
        validation_results = self.field_validator.validate_batch(data)
        for field_name, result in validation_results.items():
            if result.errors:
                issues.append(f"字段 '{field_name}' 错误: {'; '.join(result.errors)}")
            if result.warnings:
                suggestions.append(
                    f"字段 '{field_name}' 警告: {'; '.join(result.warnings)}"
                )

        # 特定字段检查
        self._check_specific_fields(data, issues, suggestions)

        return issues, suggestions

    def _check_specific_fields(
        self,
        data: Dict[str, Any],
        issues: List[str],
        suggestions: List[str],
    ):
        """检查特定字段"""
        # 井号检查
        if "井号" in data:
            well_name = str(data["井号"])
            if len(well_name) < 3:
                issues.append(f"井号过短: {well_name}")
                suggestions.append("请确认井号是否完整")

        # 井深检查
        if "井深" in data:
            try:
                depth = float(data["井深"])
                if depth < 100:
                    issues.append(f"井深过浅: {depth}米")
                if depth > 10000:
                    issues.append(f"井深异常: {depth}米")
            except ValueError:
                pass

        # 日期检查
        for field in ["开钻日期", "完钻日期", "完井日期"]:
            if field in data:
                date = self._parse_date(data[field])
                if date:
                    # 检查日期是否过于久远或过于未来
                    today = datetime.now()
                    if date < datetime(1950, 1, 1):
                        issues.append(f"{field}过早: {data[field]}")
                    if date > datetime(today.year + 1, 12, 31):
                        issues.append(f"{field}在未来: {data[field]}")

    def _parse_date(self, date_str: Any) -> Optional[datetime]:
        """解析日期"""
        if not date_str:
            return None

        formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%Y年%m月%d日",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(str(date_str), fmt)
            except ValueError:
                continue

        return None

    def batch_check_quality(
        self,
        documents: List[Dict[str, Any]],
        target_fields: List[str],
    ) -> List[QualityReport]:
        """
        批量检查数据质量

        Args:
            documents: 文档列表,每个文档包含id和data
            target_fields: 目标字段列表

        Returns:
            质量报告列表
        """
        reports = []

        for idx, doc in enumerate(documents):
            logger.info(f"质量检查进度: {idx + 1}/{len(documents)}")
            report = self.check_quality(
                document_id=doc.get("id", f"doc_{idx}"),
                extracted_data=doc.get("data", {}),
                target_fields=target_fields,
                metadata=doc.get("metadata"),
            )
            reports.append(report)

        # 统计汇总
        avg_score = sum(r.metrics.overall_score for r in reports) / len(reports)
        logger.info(
            f"批量质量检查完成,平均评分: {avg_score:.2f}"
        )

        return reports

    def get_quality_summary(
        self,
        reports: List[QualityReport],
    ) -> Dict[str, Any]:
        """
        获取质量检查摘要

        Args:
            reports: 质量报告列表

        Returns:
            摘要信息
        """
        total = len(reports)
        if total == 0:
            return {"total_documents": 0}

        high_quality = sum(1 for r in reports if r.metrics.overall_score >= 0.9)
        medium_quality = sum(
            1 for r in reports
            if 0.7 <= r.metrics.overall_score < 0.9
        )
        low_quality = sum(1 for r in reports if r.metrics.overall_score < 0.7)

        avg_completeness = sum(r.metrics.completeness for r in reports) / total
        avg_accuracy = sum(r.metrics.accuracy for r in reports) / total
        avg_consistency = sum(r.metrics.consistency for r in reports) / total
        avg_confidence = sum(r.metrics.confidence for r in reports) / total
        avg_overall = sum(r.metrics.overall_score for r in reports) / total

        total_issues = sum(len(r.issues) for r in reports)

        return {
            "total_documents": total,
            "high_quality": high_quality,
            "medium_quality": medium_quality,
            "low_quality": low_quality,
            "avg_completeness": round(avg_completeness, 3),
            "avg_accuracy": round(avg_accuracy, 3),
            "avg_consistency": round(avg_consistency, 3),
            "avg_confidence": round(avg_confidence, 3),
            "avg_overall_score": round(avg_overall, 3),
            "total_issues": total_issues,
        }
