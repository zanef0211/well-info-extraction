"""
文本清洗器 - 清理和规范化文本
"""
import logging
import re
from typing import List, Dict, Any, Optional
import string

from utils.logger import get_logger

logger = get_logger(__name__)


class TextCleaner:
    """文本清洗器 - 清理和规范化文本"""

    def __init__(
        self,
        remove_extra_spaces: bool = True,
        remove_special_chars: bool = False,
        normalize_whitespace: bool = True,
        remove_page_numbers: bool = True,
    ):
        """
        初始化文本清洗器

        Args:
            remove_extra_spaces: 是否移除多余空格
            remove_special_chars: 是否移除特殊字符
            normalize_whitespace: 是否规范化空白字符
            remove_page_numbers: 是否移除页码
        """
        self.remove_extra_spaces = remove_extra_spaces
        self.remove_special_chars = remove_special_chars
        self.normalize_whitespace = normalize_whitespace
        self.remove_page_numbers = remove_page_numbers

        # 页码正则模式
        self.page_number_patterns = [
            r"第\s*\d+\s*页",
            r"Page\s*\d+",
            r"第\d+页",
            r"^\s*\d+\s*$",  # 单独数字的行
        ]

        logger.info("文本清洗器初始化完成")

    def clean(self, text: str) -> str:
        """
        清洗文本

        Args:
            text: 原始文本

        Returns:
            清洗后的文本
        """
        if not text:
            return ""

        cleaned = text

        # 规范化空白字符
        if self.normalize_whitespace:
            cleaned = self._normalize_whitespace(cleaned)

        # 移除多余空格
        if self.remove_extra_spaces:
            cleaned = self._remove_extra_spaces(cleaned)

        # 移除页码
        if self.remove_page_numbers:
            cleaned = self._remove_page_numbers(cleaned)

        # 移除特殊字符
        if self.remove_special_chars:
            cleaned = self._remove_special_chars(cleaned)

        # 移除空行
        cleaned = self._remove_empty_lines(cleaned)

        logger.debug(f"文本清洗完成,原长度: {len(text)}, 新长度: {len(cleaned)}")
        return cleaned

    def _normalize_whitespace(self, text: str) -> str:
        """
        规范化空白字符

        Args:
            text: 文本

        Returns:
            规范化后的文本
        """
        # 统一换行符
        text = re.sub(r"\r\n|\r", "\n", text)

        # 将所有空白字符(制表符等)转换为空格
        text = re.sub(r"[ \t]+", " ", text)

        return text

    def _remove_extra_spaces(self, text: str) -> str:
        """
        移除多余空格

        Args:
            text: 文本

        Returns:
            处理后的文本
        """
        # 移除每行首尾空格
        lines = text.split("\n")
        lines = [line.strip() for line in lines]

        # 合并过多空格
        cleaned_lines = []
        for line in lines:
            # 将连续多个空格合并为一个
            line = re.sub(r" {2,}", " ", line)
            cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    def _remove_page_numbers(self, text: str) -> str:
        """
        移除页码

        Args:
            text: 文本

        Returns:
            处理后的文本
        """
        lines = text.split("\n")
        filtered_lines = []

        for line in lines:
            # 检查是否是页码行
            is_page_number = False
            for pattern in self.page_number_patterns:
                if re.match(pattern, line.strip()):
                    is_page_number = True
                    break

            if not is_page_number:
                filtered_lines.append(line)

        return "\n".join(filtered_lines)

    def _remove_special_chars(self, text: str) -> str:
        """
        移除特殊字符(保留中文、英文、数字、常用标点)

        Args:
            text: 文本

        Returns:
            处理后的文本
        """
        # 保留: 中文、英文、数字、常用标点
        pattern = r"[^\u4e00-\u9fff\u3000-\u303fa-zA-Z0-9\s.,;:!?()（）【】「」'\"、。，;：！？]"
        cleaned = re.sub(pattern, "", text)

        return cleaned

    def _remove_empty_lines(self, text: str) -> str:
        """
        移除空行

        Args:
            text: 文本

        Returns:
            处理后的文本
        """
        lines = text.split("\n")
        # 过滤空行,但保留段落分隔(连续空行最多保留一个)
        filtered_lines = []
        prev_empty = False

        for line in lines:
            if line.strip():
                filtered_lines.append(line)
                prev_empty = False
            else:
                if not prev_empty:
                    filtered_lines.append(line)
                prev_empty = True

        return "\n".join(filtered_lines)

    def extract_numbers(self, text: str) -> List[float]:
        """
        提取文本中的所有数字

        Args:
            text: 文本

        Returns:
            数字列表
        """
        # 匹配整数和小数
        pattern = r"\d+\.?\d*"
        matches = re.findall(pattern, text)

        numbers = [float(match) for match in matches]
        logger.debug(f"提取到 {len(numbers)} 个数字")
        return numbers

    def extract_dates(self, text: str) -> List[str]:
        """
        提取文本中的日期

        Args:
            text: 文本

        Returns:
            日期字符串列表
        """
        # 匹配常见日期格式: YYYY-MM-DD, YYYY/MM/DD, YYYY年MM月DD日
        patterns = [
            r"\d{4}-\d{1,2}-\d{1,2}",
            r"\d{4}/\d{1,2}/\d{1,2}",
            r"\d{4}年\d{1,2}月\d{1,2}日",
        ]

        dates = []
        for pattern in patterns:
            dates.extend(re.findall(pattern, text))

        # 去重
        dates = list(set(dates))
        logger.debug(f"提取到 {len(dates)} 个日期")
        return dates

    def extract_units(self, text: str) -> List[str]:
        """
        提取文本中的单位

        Args:
            text: 文本

        Returns:
            单位列表
        """
        # 常用单位
        units = [
            "米", "m", "mm", "cm", "km",
            "吨", "t", "kg", "g",
            "MPa", "Pa", "kPa",
            "摄氏度", "℃", "°C",
            "立方米", "m³",
            "升", "L",
            "小时", "h", "min", "s",
            "rpm", "bar", "psi",
            "%",
        ]

        found_units = []
        for unit in units:
            if unit in text:
                found_units.append(unit)

        logger.debug(f"提取到 {len(found_units)} 个单位")
        return found_units

    def segment_by_keywords(
        self,
        text: str,
        keywords: List[str],
        keep_headers: bool = True,
    ) -> Dict[str, str]:
        """
        按关键词分段

        Args:
            text: 文本
            keywords: 关键词列表
            keep_headers: 是否保留关键词作为标题

        Returns:
            分段结果字典 {关键词: 内容}
        """
        segments = {}

        # 构建正则模式
        pattern = "|".join([re.escape(kw) for kw in keywords])

        # 分割文本
        parts = re.split(pattern, text, flags=re.IGNORECASE)

        # 提取标题(关键词)
        titles = re.findall(pattern, text, flags=re.IGNORECASE)

        # 配对标题和内容
        for i, title in enumerate(titles):
            content = parts[i + 1] if i + 1 < len(parts) else ""
            segments[title] = content.strip()

        logger.debug(f"按关键词分段,共 {len(segments)} 段")
        return segments

    def merge_lines(
        self,
        text: str,
        max_line_length: Optional[int] = None,
    ) -> str:
        """
        合并短行(修复OCR导致的换行问题)

        Args:
            text: 文本
            max_line_length: 最大行长,超过则不合并

        Returns:
            合并后的文本
        """
        lines = text.split("\n")
        merged_lines = []

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # 检查是否应该与下一行合并
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()

                # 如果当前行较短,且下一行也较短,则合并
                should_merge = False
                if max_line_length and len(line) < max_line_length:
                    # 检查下一行是否以小写字母开头(可能是同一句)
                    if next_line and next_line[0].islower():
                        should_merge = True
                    # 检查是否以标点符号结尾
                    elif not line or line[-1] not in "。.！!?？,，":
                        should_merge = True

                if should_merge:
                    merged_line = line + next_line
                    merged_lines.append(merged_line)
                    i += 2
                    continue

            merged_lines.append(line)
            i += 1

        return "\n".join(merged_lines)
