"""
规则检查器 - 检查业务规则和逻辑一致性
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

from config.field_schemas import FIELD_SCHEMAS, DOCUMENT_TYPES
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RuleResult:
    """规则检查结果"""
    rule_name: str
    is_passed: bool
    message: str
    severity: str  # error, warning, info
    affected_fields: List[str]


class RuleChecker:
    """规则检查器 - 检查业务规则和逻辑一致性"""

    def __init__(self):
        """初始化规则检查器"""
        self.rules = self._define_rules()
        logger.info(f"规则检查器初始化完成,共 {len(self.rules)} 条规则")

    def _define_rules(self) -> List[Dict[str, Any]]:
        """定义业务规则"""
        return [
            {
                "name": "日期顺序",
                "description": "开钻日期不能晚于完钻/完井日期",
                "check": self._check_date_order,
                "fields": ["开钻日期", "完钻日期", "完井日期"],
                "severity": "error",
            },
            {
                "name": "井深关系",
                "description": "斜深应大于等于垂深",
                "check": self._check_depth_relation,
                "fields": ["斜深", "垂深"],
                "severity": "error",
            },
            {
                "name": "位移范围",
                "description": "位移不应超过斜深的90%",
                "check": self._check_displacement,
                "fields": ["位移", "斜深"],
                "severity": "warning",
            },
            {
                "name": "压力温度",
                "description": "地层温度应随深度增加而增加",
                "check": self._check_temp_gradient,
                "fields": ["地层温度", "垂深"],
                "severity": "warning",
            },
            {
                "name": "必填字段",
                "description": "根据文档类型检查必填字段",
                "check": self._check_required_fields,
                "fields": [],
                "severity": "error",
            },
            {
                "name": "井号格式",
                "description": "井号应符合命名规范",
                "check": self._check_well_name_format,
                "fields": ["井号"],
                "severity": "warning",
            },
        ]

    def check(
        self,
        data: Dict[str, Any],
        document_type: Optional[str] = None,
    ) -> List[RuleResult]:
        """
        检查所有规则

        Args:
            data: 字段数据
            document_type: 文档类型

        Returns:
            规则检查结果列表
        """
        results = []

        for rule in self.rules:
            try:
                rule_name = rule["name"]
                logger.debug(f"检查规则: {rule_name}")

                # 执行规则检查
                passed, message, affected = rule["check"](data, document_type)

                result = RuleResult(
                    rule_name=rule_name,
                    is_passed=passed,
                    message=message,
                    severity=rule["severity"],
                    affected_fields=affected,
                )
                results.append(result)

                if not passed:
                    logger.warning(f"规则检查失败: {rule_name} - {message}")

            except Exception as e:
                logger.error(f"规则检查异常: {rule['name']}, {e}", exc_info=True)
                results.append(RuleResult(
                    rule_name=rule["name"],
                    is_passed=False,
                    message=f"规则检查异常: {str(e)}",
                    severity="error",
                    affected_fields=rule.get("fields", []),
                ))

        return results

    def _check_date_order(
        self,
        data: Dict[str, Any],
        document_type: Optional[str],
    ) -> Tuple[bool, str, List[str]]:
        """检查日期顺序"""
        # 获取相关日期字段
        date_fields = {
            "开钻日期": None,
            "完钻日期": None,
            "完井日期": None,
        }

        for field_name in date_fields.keys():
            if field_name in data and data[field_name]:
                try:
                    date_fields[field_name] = self._parse_date(data[field_name])
                except Exception:
                    continue

        # 检查顺序
        errors = []
        affected_fields = []

        if date_fields["开钻日期"] and date_fields["完钻日期"]:
            if date_fields["开钻日期"] > date_fields["完钻日期"]:
                errors.append("开钻日期晚于完钻日期")
                affected_fields.extend(["开钻日期", "完钻日期"])

        if date_fields["开钻日期"] and date_fields["完井日期"]:
            if date_fields["开钻日期"] > date_fields["完井日期"]:
                errors.append("开钻日期晚于完井日期")
                affected_fields.extend(["开钻日期", "完井日期"])

        if date_fields["完钻日期"] and date_fields["完井日期"]:
            if date_fields["完钻日期"] > date_fields["完井日期"]:
                errors.append("完钻日期晚于完井日期")
                affected_fields.extend(["完钻日期", "完井日期"])

        if errors:
            return False, "; ".join(errors), list(set(affected_fields))
        return True, "日期顺序正确", []

    def _check_depth_relation(
        self,
        data: Dict[str, Any],
        document_type: Optional[str],
    ) -> Tuple[bool, str, List[str]]:
        """检查井深关系: 斜深 >= 垂深"""
        oblique_depth = self._get_number(data.get("斜深"))
        vertical_depth = self._get_number(data.get("垂深"))

        if oblique_depth is None or vertical_depth is None:
            return True, "缺少井深数据,跳过检查", []

        if oblique_depth < vertical_depth:
            return False, f"斜深({oblique_depth})小于垂深({vertical_depth})", ["斜深", "垂深"]

        return True, "井深关系正确", []

    def _check_displacement(
        self,
        data: Dict[str, Any],
        document_type: Optional[str],
    ) -> Tuple[bool, str, List[str]]:
        """检查位移范围"""
        displacement = self._get_number(data.get("位移"))
        oblique_depth = self._get_number(data.get("斜深"))

        if displacement is None or oblique_depth is None:
            return True, "缺少位移或斜深数据,跳过检查", []

        # 位移不应超过斜深的90%
        max_displacement = oblique_depth * 0.9
        if displacement > max_displacement:
            return (
                False,
                f"位移({displacement})超过斜深({oblique_depth})的90%",
                ["位移", "斜深"]
            )

        return True, "位移在合理范围内", []

    def _check_temp_gradient(
        self,
        data: Dict[str, Any],
        document_type: Optional[str],
    ) -> Tuple[bool, str, List[str]]:
        """检查温度梯度"""
        # 地层温度应随深度增加
        # 简化检查: 如果有多条记录,检查温度递增

        # 单条数据无法检查
        return True, "单条数据无法检查温度梯度", []

    def _check_required_fields(
        self,
        data: Dict[str, Any],
        document_type: Optional[str],
    ) -> Tuple[bool, str, List[str]]:
        """检查必填字段"""
        if not document_type or document_type not in DOCUMENT_TYPES:
            return True, "未指定文档类型,跳过检查", []

        # 获取文档类型的必填字段
        doc_info = DOCUMENT_TYPES[document_type]
        required_fields = doc_info.get("required_fields", [])

        missing_fields = []
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == "":
                missing_fields.append(field)

        if missing_fields:
            return False, f"缺少必填字段: {', '.join(missing_fields)}", missing_fields

        return True, "所有必填字段均已填写", []

    def _check_well_name_format(
        self,
        data: Dict[str, Any],
        document_type: Optional[str],
    ) -> Tuple[bool, str, List[str]]:
        """检查井号格式"""
        well_name = data.get("井号")
        if not well_name:
            return True, "未提供井号,跳过检查", []

        import re

        # 常见井号格式
        valid_patterns = [
            r"^.+-\d+-\d+$",  # XXX-1-1
            r"^.+\d+$",  # XXX1
            r"^.+\d+-\d+$",  # XXX1-1
            r"^.*井$",  # XXX井
        ]

        is_valid = any(re.match(p, str(well_name)) for p in valid_patterns)

        if not is_valid:
            return (
                False,
                f"井号格式可能不标准: {well_name}",
                ["井号"]
            )

        return True, "井号格式正确", ["井号"]

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """解析日期字符串"""
        if not date_str:
            return None

        formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%Y年%m月%d日",
            "%Y%m%d",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(str(date_str), fmt)
            except ValueError:
                continue

        return None

    def _get_number(self, value: Any) -> Optional[float]:
        """获取数值"""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def get_rule_summary(
        self,
        results: List[RuleResult],
    ) -> Dict[str, Any]:
        """
        获取规则检查摘要

        Args:
            results: 规则检查结果列表

        Returns:
            摘要信息
        """
        total = len(results)
        passed = sum(1 for r in results if r.is_passed)
        failed = total - passed

        errors = sum(1 for r in results if not r.is_passed and r.severity == "error")
        warnings = sum(1 for r in results if not r.is_passed and r.severity == "warning")

        # 收集所有受影响的字段
        all_affected_fields = []
        for result in results:
            all_affected_fields.extend(result.affected_fields)
        all_affected_fields = list(set(all_affected_fields))

        return {
            "total_rules": total,
            "passed_rules": passed,
            "failed_rules": failed,
            "error_count": errors,
            "warning_count": warnings,
            "pass_rate": round(passed / total * 100, 2) if total > 0 else 0,
            "affected_fields": all_affected_fields,
        }
