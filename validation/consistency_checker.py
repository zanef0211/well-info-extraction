"""
一致性检查器 - 检查字段间的逻辑一致性
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ConsistencyCheck:
    """一致性检查结果"""
    check_name: str
    is_consistent: bool
    message: str
    involved_fields: List[str]
    severity: str  # error, warning, info


class ConsistencyChecker:
    """一致性检查器"""

    def __init__(self):
        """初始化一致性检查器"""
        self.checks = self._define_checks()
        logger.info(f"一致性检查器初始化完成,共 {len(self.checks)} 个检查项")

    def _define_checks(self) -> List[Dict[str, Any]]:
        """定义一致性检查项"""
        return [
            {
                "name": "井深关系",
                "description": "斜深应大于等于垂深",
                "check": self._check_depth_relation,
            },
            {
                "name": "位移限制",
                "description": "位移不应超过斜深",
                "check": self._check_displacement_limit,
            },
            {
                "name": "日期逻辑",
                "description": "开钻日期 <= 完钻日期 <= 完井日期",
                "check": self._check_date_logic,
            },
            {
                "name": "井位坐标",
                "description": "井位坐标应在合理范围内",
                "check": self._check_coordinates,
            },
            {
                "name": "压力温度",
                "description": "地层压力和温度应随深度增加",
                "check": self._check_pressure_temp,
            },
            {
                "name": "钻井参数",
                "description": "钻井参数应在合理范围内",
                "check": self._check_drilling_params,
            },
        ]

    def check(
        self,
        data: Dict[str, Any],
    ) -> List[ConsistencyCheck]:
        """
        检查数据一致性

        Args:
            data: 字段数据

        Returns:
            一致性检查结果列表
        """
        results = []

        for check_def in self.checks:
            try:
                logger.debug(f"执行一致性检查: {check_def['name']}")

                check = check_def["check"]
                result = check(data)

                results.append(result)

                if not result.is_consistent:
                    logger.warning(
                        f"一致性检查失败: {check_def['name']} - {result.message}"
                    )

            except Exception as e:
                logger.error(
                    f"一致性检查异常: {check_def['name']}, {e}",
                    exc_info=True
                )
                results.append(ConsistencyCheck(
                    check_name=check_def["name"],
                    is_consistent=False,
                    message=f"检查异常: {str(e)}",
                    involved_fields=[],
                    severity="error",
                ))

        return results

    def _check_depth_relation(self, data: Dict[str, Any]) -> ConsistencyCheck:
        """检查井深关系: 斜深 >= 垂深"""
        oblique = self._get_number(data.get("斜深"))
        vertical = self._get_number(data.get("垂深"))

        if oblique is None or vertical is None:
            return ConsistencyCheck(
                check_name="井深关系",
                is_consistent=True,
                message="缺少井深数据,跳过检查",
                involved_fields=["斜深", "垂深"],
                severity="info",
            )

        if oblique < vertical:
            return ConsistencyCheck(
                check_name="井深关系",
                is_consistent=False,
                message=f"斜深({oblique}m)小于垂深({vertical}m)",
                involved_fields=["斜深", "垂深"],
                severity="error",
            )

        return ConsistencyCheck(
            check_name="井深关系",
            is_consistent=True,
            message=f"井深关系正确: 斜深{oblique}m >= 垂深{vertical}m",
            involved_fields=["斜深", "垂深"],
            severity="info",
        )

    def _check_displacement_limit(self, data: Dict[str, Any]) -> ConsistencyCheck:
        """检查位移限制: 位移不应超过斜深"""
        displacement = self._get_number(data.get("位移"))
        oblique = self._get_number(data.get("斜深"))

        if displacement is None or oblique is None:
            return ConsistencyCheck(
                check_name="位移限制",
                is_consistent=True,
                message="缺少位移或斜深数据,跳过检查",
                involved_fields=["位移", "斜深"],
                severity="info",
            )

        if displacement > oblique:
            return ConsistencyCheck(
                check_name="位移限制",
                is_consistent=False,
                message=f"位移({displacement}m)超过斜深({oblique}m)",
                involved_fields=["位移", "斜深"],
                severity="error",
            )

        # 检查位移是否过大(超过斜深的90%)
        if displacement > oblique * 0.9:
            return ConsistencyCheck(
                check_name="位移限制",
                is_consistent=False,
                message=f"位移({displacement}m)接近斜深({oblique}m)的90%,可能异常",
                involved_fields=["位移", "斜深"],
                severity="warning",
            )

        return ConsistencyCheck(
            check_name="位移限制",
            is_consistent=True,
            message=f"位移({displacement}m)在合理范围内",
            involved_fields=["位移", "斜深"],
            severity="info",
        )

    def _check_date_logic(self, data: Dict[str, Any]) -> ConsistencyCheck:
        """检查日期逻辑: 开钻 <= 完钻 <= 完井"""
        dates = {
            "开钻日期": self._parse_date(data.get("开钻日期")),
            "完钻日期": self._parse_date(data.get("完钻日期")),
            "完井日期": self._parse_date(data.get("完井日期")),
        }

        # 过滤掉None
        dates = {k: v for k, v in dates.items() if v is not None}

        if len(dates) < 2:
            return ConsistencyCheck(
                check_name="日期逻辑",
                is_consistent=True,
                message="日期数据不足,跳过检查",
                involved_fields=list(dates.keys()),
                severity="info",
            )

        # 排序日期
        sorted_dates = sorted(dates.items(), key=lambda x: x[1])

        # 检查顺序
        expected_order = ["开钻日期", "完钻日期", "完井日期"]
        actual_order = [name for name, _ in sorted_dates]

        issues = []
        for i in range(len(sorted_dates) - 1):
            name1, date1 = sorted_dates[i]
            name2, date2 = sorted_dates[i + 1]

            # 检查是否符合预期顺序
            if name1 in expected_order and name2 in expected_order:
                idx1 = expected_order.index(name1)
                idx2 = expected_order.index(name2)

                if idx1 > idx2:
                    issues.append(
                        f"{name1}({date1.strftime('%Y-%m-%d')}) "
                        f"晚于 {name2}({date2.strftime('%Y-%m-%d')})"
                    )

        if issues:
            return ConsistencyCheck(
                check_name="日期逻辑",
                is_consistent=False,
                message="; ".join(issues),
                involved_fields=list(dates.keys()),
                severity="error",
            )

        return ConsistencyCheck(
            check_name="日期逻辑",
            is_consistent=True,
            message=f"日期顺序正确: {' -> '.join(actual_order)}",
            involved_fields=list(dates.keys()),
            severity="info",
        )

    def _check_coordinates(self, data: Dict[str, Any]) -> ConsistencyCheck:
        """检查井位坐标"""
        # 支持多种坐标格式
        lon = None
        lat = None

        # 尝试解析经度
        for field in ["经度", "Longitude", "东经"]:
            if field in data:
                lon = self._get_number(data[field])
                if lon is not None:
                    break

        # 尝试解析纬度
        for field in ["纬度", "Latitude", "北纬"]:
            if field in data:
                lat = self._get_number(data[field])
                if lat is not None:
                    break

        if lon is None or lat is None:
            return ConsistencyCheck(
                check_name="井位坐标",
                is_consistent=True,
                message="缺少坐标数据,跳过检查",
                involved_fields=["经度", "纬度"],
                severity="info",
            )

        issues = []

        # 检查经度范围 (-180, 180)
        if not (-180 <= lon <= 180):
            issues.append(f"经度({lon})超出范围(-180, 180)")

        # 检查纬度范围 (-90, 90)
        if not (-90 <= lat <= 90):
            issues.append(f"纬度({lat})超出范围(-90, 90)")

        # 检查中国境内范围(可选)
        # 中国大致范围: 经度 73-135, 纬度 18-54
        if not (73 <= lon <= 135) or not (18 <= lat <= 54):
            issues.append(
                f"坐标({lon}, {lat})可能不在中国境内,"
                f"中国范围: 经度73-135, 纬度18-54"
            )

        if issues:
            return ConsistencyCheck(
                check_name="井位坐标",
                is_consistent=False,
                message="; ".join(issues),
                involved_fields=["经度", "纬度"],
                severity="warning" if len(issues) == 1 else "error",
            )

        return ConsistencyCheck(
            check_name="井位坐标",
            is_consistent=True,
            message=f"坐标({lon}, {lat})在合理范围内",
            involved_fields=["经度", "纬度"],
            severity="info",
        )

    def _check_pressure_temp(self, data: Dict[str, Any]) -> ConsistencyCheck:
        """检查压力温度随深度的变化"""
        # 如果有多条记录(不同深度),检查趋势
        # 单条数据无法检查
        return ConsistencyCheck(
            check_name="压力温度",
            is_consistent=True,
            message="单条数据无法检查压力温度趋势",
            involved_fields=["地层压力", "地层温度", "垂深"],
            severity="info",
        )

    def _check_drilling_params(self, data: Dict[str, Any]) -> ConsistencyCheck:
        """检查钻井参数的合理性"""
        params = {
            "钻压": ("钻压(kN)", 0, 1000),
            "转速": ("转速(rpm)", 0, 500),
            "泵压": ("泵压(MPa)", 0, 50),
            "排量": ("排量(L/s)", 0, 100),
        }

        issues = []

        for field, (unit, min_val, max_val) in params.items():
            value = self._get_number(data.get(field))
            if value is not None:
                if value < min_val or value > max_val:
                    issues.append(
                        f"{field}({value}{unit})超出合理范围({min_val}-{max_val})"
                    )

        if issues:
            return ConsistencyCheck(
                check_name="钻井参数",
                is_consistent=False,
                message="; ".join(issues),
                involved_fields=list(params.keys()),
                severity="warning",
            )

        return ConsistencyCheck(
            check_name="钻井参数",
            is_consistent=True,
            message="钻井参数在合理范围内",
            involved_fields=[],
            severity="info",
        )

    def _get_number(self, value: Any) -> Optional[float]:
        """获取数值"""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _parse_date(self, value: Any) -> Optional["datetime"]:
        """解析日期"""
        if value is None:
            return None

        from datetime import datetime

        formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%Y年%m月%d日",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(str(value), fmt)
            except ValueError:
                continue

        return None

    def get_consistency_summary(
        self,
        checks: List[ConsistencyCheck],
    ) -> Dict[str, Any]:
        """
        获取一致性检查摘要

        Args:
            checks: 一致性检查结果列表

        Returns:
            摘要信息
        """
        total = len(checks)
        consistent = sum(1 for c in checks if c.is_consistent)
        inconsistent = total - consistent

        errors = sum(1 for c in checks if not c.is_consistent and c.severity == "error")
        warnings = sum(1 for c in checks if not c.is_consistent and c.severity == "warning")

        # 收集所有涉及的字段
        all_fields = []
        for check in checks:
            all_fields.extend(check.involved_fields)
        all_fields = list(set(all_fields))

        return {
            "total_checks": total,
            "consistent_checks": consistent,
            "inconsistent_checks": inconsistent,
            "error_count": errors,
            "warning_count": warnings,
            "consistency_rate": round(consistent / total * 100, 2) if total > 0 else 0,
            "involved_fields": all_fields,
        }
