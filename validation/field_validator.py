"""
字段验证器 - 验证字段值的格式、范围、合理性
"""
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

from config.field_schemas import FIELD_SCHEMAS
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    field_name: str
    field_value: Any
    errors: List[str]
    warnings: List[str]
    confidence: float = 0.0


class FieldValidator:
    """字段验证器 - 验证字段值的格式和合理性"""

    def __init__(self):
        """初始化字段验证器"""
        self.field_schemas = FIELD_SCHEMAS
        logger.info("字段验证器初始化完成")

    def validate(
        self,
        field_name: str,
        field_value: Any,
        document_type: Optional[str] = None,
    ) -> ValidationResult:
        """
        验证字段值

        Args:
            field_name: 字段名称
            field_value: 字段值
            document_type: 文档类型(用于获取文档特定规则)

        Returns:
            验证结果
        """
        errors = []
        warnings = []
        confidence = 0.0

        # 检查字段是否存在Schema
        if field_name not in self.field_schemas:
            errors.append(f"未知的字段类型: {field_name}")
            return ValidationResult(
                is_valid=False,
                field_name=field_name,
                field_value=field_value,
                errors=errors,
                warnings=warnings,
                confidence=0.0,
            )

        schema = self.field_schemas[field_name]
        field_type = schema["type"]

        # 1. 检查字段是否为空
        if field_value is None or field_value == "":
            if schema.get("required", False):
                errors.append(f"必填字段为空: {field_name}")
            else:
                warnings.append(f"字段为空(非必填): {field_name}")
            return ValidationResult(
                is_valid=False if schema.get("required", False) else True,
                field_name=field_name,
                field_value=field_value,
                errors=errors,
                warnings=warnings,
                confidence=0.0,
            )

        # 2. 根据字段类型进行验证
        if field_type == "string":
            valid, conf, errs, warns = self._validate_string(field_value, schema)
        elif field_type == "number":
            valid, conf, errs, warns = self._validate_number(field_value, schema)
        elif field_type == "date":
            valid, conf, errs, warns = self._validate_date(field_value, schema)
        elif field_type == "enum":
            valid, conf, errs, warns = self._validate_enum(field_value, schema)
        elif field_type == "coordinates":
            valid, conf, errs, warns = self._validate_coordinates(field_value, schema)
        else:
            errors.append(f"不支持的字段类型: {field_type}")
            return ValidationResult(
                is_valid=False,
                field_name=field_name,
                field_value=field_value,
                errors=errors,
                warnings=warnings,
                confidence=0.0,
            )

        errors.extend(errs)
        warnings.extend(warns)
        confidence = conf

        # 3. 自定义验证规则
        custom_valid, custom_conf, custom_errs, custom_warns = self._validate_custom_rules(
            field_name, field_value, schema, document_type
        )
        if not custom_valid:
            errors.extend(custom_errs)
        warnings.extend(custom_warns)

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            field_name=field_name,
            field_value=field_value,
            errors=errors,
            warnings=warnings,
            confidence=confidence,
        )

    def _validate_string(
        self,
        value: Any,
        schema: Dict,
    ) -> Tuple[bool, float, List[str], List[str]]:
        """验证字符串类型"""
        errors = []
        warnings = []

        # 转换为字符串
        if not isinstance(value, str):
            try:
                value = str(value)
            except Exception as e:
                return False, 0.0, [f"无法转换为字符串: {e}"], []

        # 检查长度
        min_length = schema.get("min_length")
        max_length = schema.get("max_length")

        if min_length and len(value) < min_length:
            errors.append(f"字符串长度不足: {len(value)} < {min_length}")
        if max_length and len(value) > max_length:
            errors.append(f"字符串长度超限: {len(value)} > {max_length}")

        # 检查格式(正则)
        pattern = schema.get("pattern")
        if pattern and value:
            if not re.match(pattern, value):
                errors.append(f"格式不符合要求: {schema.get('pattern_desc', pattern)}")

        # 井号格式验证
        field_name = schema.get("name")
        if field_name and "井" in field_name:
            if self._is_valid_well_name(value):
                confidence = 0.9
            else:
                warnings.append(f"井号格式可能不标准: {value}")
                confidence = 0.5
        else:
            confidence = 0.8

        return len(errors) == 0, confidence, errors, warnings

    def _validate_number(
        self,
        value: Any,
        schema: Dict,
    ) -> Tuple[bool, float, List[str], List[str]]:
        """验证数字类型"""
        errors = []
        warnings = []

        # 尝试转换为浮点数
        try:
            num_value = float(value)
        except (ValueError, TypeError):
            return False, 0.0, [f"无法转换为数字: {value}"], []

        # 检查范围
        min_value = schema.get("min_value")
        max_value = schema.get("max_value")

        if min_value is not None and num_value < min_value:
            errors.append(f"数值过小: {num_value} < {min_value}")
        if max_value is not None and num_value > max_value:
            errors.append(f"数值过大: {num_value} > {max_value}")

        # 检查合理性(基于常见值域)
        reasonable = self._check_reasonable_range(schema.get("name", ""), num_value)
        if not reasonable:
            warnings.append(f"数值可能超出合理范围: {num_value}")

        confidence = 0.9 if len(errors) == 0 else 0.3
        return len(errors) == 0, confidence, errors, warnings

    def _validate_date(
        self,
        value: Any,
        schema: Dict,
    ) -> Tuple[bool, float, List[str], List[str]]:
        """验证日期类型"""
        errors = []
        warnings = []

        # 支持的日期格式
        date_formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%Y年%m月%d日",
            "%Y%m%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
        ]

        parsed_date = None
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(str(value), fmt)
                break
            except ValueError:
                continue

        if parsed_date is None:
            errors.append(f"无法解析日期: {value}")
            return False, 0.0, errors, warnings

        # 检查日期合理性
        today = datetime.now()
        min_date = datetime(1900, 1, 1)
        max_date = datetime(today.year + 1, 12, 31)

        if parsed_date < min_date:
            warnings.append(f"日期过早: {value}")
        if parsed_date > max_date:
            errors.append(f"日期在未来: {value}")

        confidence = 0.95 if len(errors) == 0 else 0.4
        return len(errors) == 0, confidence, errors, warnings

    def _validate_enum(
        self,
        value: Any,
        schema: Dict,
    ) -> Tuple[bool, float, List[str], List[str]]:
        """验证枚举类型"""
        errors = []
        warnings = []

        allowed_values = schema.get("allowed_values", [])
        if not allowed_values:
            return True, 0.5, [], ["未定义枚举值列表"]

        value_str = str(value).strip()
        if value_str not in allowed_values:
            errors.append(f"值不在允许范围内: {value_str}")
            return False, 0.0, errors, warnings

        return True, 1.0, [], []

    def _validate_coordinates(
        self,
        value: Any,
        schema: Dict,
    ) -> Tuple[bool, float, List[str], List[str]]:
        """验证坐标类型"""
        errors = []
        warnings = []

        # 支持多种坐标格式
        # 1. "经度,纬度" 或 "纬度,经度"
        # 2. "经度 纬度"
        # 3. {"lon": x, "lat": y}

        coords = None
        if isinstance(value, str):
            # 尝试解析字符串坐标
            parts = re.split(r"[,\s]+", value.strip())
            if len(parts) == 2:
                try:
                    lon, lat = float(parts[0]), float(parts[1])
                    # 检查范围
                    if -180 <= lon <= 180 and -90 <= lat <= 90:
                        coords = (lon, lat)
                    elif -90 <= lon <= 90 and -180 <= lat <= 180:
                        # 可能是 "纬度,经度" 格式
                        coords = (lat, lon)
                except ValueError:
                    pass
        elif isinstance(value, dict):
            lon = value.get("lon") or value.get("longitude")
            lat = value.get("lat") or value.get("latitude")
            if lon is not None and lat is not None:
                coords = (float(lon), float(lat))

        if coords is None:
            errors.append(f"无法解析坐标: {value}")
            return False, 0.0, errors, warnings

        # 验证坐标范围
        lon, lat = coords
        if not (-180 <= lon <= 180):
            errors.append(f"经度超出范围: {lon}")
        if not (-90 <= lat <= 90):
            errors.append(f"纬度超出范围: {lat}")

        confidence = 0.9 if len(errors) == 0 else 0.3
        return len(errors) == 0, confidence, errors, warnings

    def _is_valid_well_name(self, well_name: str) -> bool:
        """检查井号格式是否合理"""
        # 常见井号格式: XXX-1-1, XXX井, XXX1井等
        patterns = [
            r"^.+-\d+-\d+$",  # XXX-1-1
            r"^.+\d+$",  # XXX1
            r"^.+\d+-\d+$",  # XXX1-1
            r"^.*井$",  # XXX井
        ]
        return any(re.match(p, well_name) for p in patterns)

    def _check_reasonable_range(self, field_name: str, value: float) -> bool:
        """检查数值是否在合理范围内"""
        # 常见字段的合理范围
        reasonable_ranges = {
            "井深": (0, 10000),  # 米
            "位移": (0, 5000),
            "斜深": (0, 10000),
            "垂深": (0, 10000),
            "井径": (0, 1000),  # mm
            "密度": (0, 5),  # g/cm³
            "粘度": (0, 1000),  # mPa·s
            "压力": (0, 200),  # MPa
            "温度": (-50, 200),  # 摄氏度
            "钻压": (0, 1000),  # kN
            "转速": (0, 500),  # rpm
            "泵压": (0, 50),  # MPa
            "排量": (0, 100),  # L/s
        }

        for key, (min_val, max_val) in reasonable_ranges.items():
            if key in field_name:
                return min_val <= value <= max_val

        # 默认返回True
        return True

    def _validate_custom_rules(
        self,
        field_name: str,
        field_value: Any,
        schema: Dict,
        document_type: Optional[str],
    ) -> Tuple[bool, float, List[str], List[str]]:
        """自定义验证规则"""
        errors = []
        warnings = []
        confidence = 0.0

        # 井号验证: 必须包含中文或字母数字组合
        if "井" in field_name:
            if isinstance(field_value, str):
                if not re.search(r"[\u4e00-\u9fff]|[a-zA-Z]", field_value):
                    errors.append(f"井号格式异常: 缺少中文字符或字母")

        # 日期合理性: 完井日期不能早于开钻日期
        # 这需要跨字段验证,在ConsistencyChecker中处理

        return True, confidence, errors, warnings

    def validate_batch(
        self,
        data: Dict[str, Any],
        document_type: Optional[str] = None,
    ) -> Dict[str, ValidationResult]:
        """
        批量验证字段

        Args:
            data: 字段数据字典
            document_type: 文档类型

        Returns:
            验证结果字典
        """
        results = {}

        for field_name, field_value in data.items():
            result = self.validate(field_name, field_value, document_type)
            results[field_name] = result

        # 统计
        valid_count = sum(1 for r in results.values() if r.is_valid)
        logger.info(
            f"批量验证完成: {valid_count}/{len(results)} 个字段通过验证"
        )

        return results

    def get_validation_summary(
        self,
        results: Dict[str, ValidationResult],
    ) -> Dict[str, Any]:
        """
        获取验证结果摘要

        Args:
            results: 验证结果字典

        Returns:
            摘要信息
        """
        total = len(results)
        valid = sum(1 for r in results.values() if r.is_valid)
        invalid = total - valid

        total_errors = sum(len(r.errors) for r in results.values())
        total_warnings = sum(len(r.warnings) for r in results.values())

        avg_confidence = (
            sum(r.confidence for r in results.values()) / total
            if total > 0 else 0.0
        )

        # 统计问题字段
        problem_fields = [
            name for name, result in results.items()
            if not result.is_valid
        ]

        return {
            "total_fields": total,
            "valid_fields": valid,
            "invalid_fields": invalid,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "validation_rate": round(valid / total * 100, 2) if total > 0 else 0,
            "avg_confidence": round(avg_confidence, 3),
            "problem_fields": problem_fields,
        }
